"""Independent format boundary parser; decoding bytes is Apache Arrow's job.
Spec: facebook/zstd v1.5.7 doc/zstd_compression_format.md.
Only known-size, dictionary-free, standard frames are valid in this model.
"""
def check_frame(payload, expected):
    at=0
    def take(n):
        nonlocal at
        if at+n>len(payload):raise ValueError('truncated frame')
        value=payload[at:at+n];at+=n;return value
    if take(4)!=b'\x28\xb5\x2f\xfd':raise ValueError('not a standard frame')
    descriptor=take(1)[0]
    if descriptor&0x18:raise ValueError('unused/reserved bit not produced by model')
    single=bool(descriptor&0x20);size_flag=descriptor>>6
    if not single:take(1) # window descriptor is not an allocation instruction here
    dictionary_size=[0,1,2,4][descriptor&3]
    dictionary=int.from_bytes(take(dictionary_size),'little')
    if dictionary:raise ValueError('model has no dictionary')
    size_size=([1 if single else 0,2,4,8])[size_flag]
    if not size_size:raise ValueError('unknown content size')
    size=int.from_bytes(take(size_size),'little')+(256 if size_size==2 else 0)
    if size!=expected or not 0<size<=64*1024*1024:raise ValueError('content size or budget')
    while True:
        header=int.from_bytes(take(3),'little');kind=(header>>1)&3;count=header>>3
        if kind==3 or count>128*1024:raise ValueError('block type or bound')
        take(1 if kind==1 else count)
        if header&1:break
    if descriptor&4:take(4)
    if at!=len(payload):raise ValueError('trailing bytes or concatenated frames')
    return True

if __name__=='__main__':
    import unittest
    class BoundaryTests(unittest.TestCase):
        def test_handmade_raw_and_rle(self):
            for kind,body in [(0,b'abcdef'),(1,b'a')]:
                frame=b'\x28\xb5\x2f\xfd\x20\x06'+(1+(kind<<1)+(6<<3)).to_bytes(3,'little')+body
                self.assertTrue(check_frame(frame,6))
                for n in range(len(frame)):
                    with self.assertRaises(ValueError):check_frame(frame[:n],6)
                for extra in [b'\x00',frame]:
                    with self.assertRaises(ValueError):check_frame(frame+extra,6)
                with self.assertRaises(ValueError):check_frame(frame,7)
        def test_bad_headers_and_blocks(self):
            vectors=[b'\x50\x2a\x4d\x18\x00\x00\x00\x00',b'\x28\xb5\x2f\xfd\x00\x00',
                b'\x28\xb5\x2f\xfd\x28\x06',b'\x28\xb5\x2f\xfd\x20\x06\x07\x00\x00']
            for frame in vectors:
                with self.assertRaises(ValueError):check_frame(frame,6)
        def test_arrow_frames_varied_sizes(self):
            import pyarrow
            codec=pyarrow.Codec('zstd',compression_level=1)
            for size in [1,255,256,4096,200000,1000000]:
                frame=bytes(codec.compress(b'x'*size))
                self.assertTrue(check_frame(frame,size))
                with self.assertRaises(ValueError):check_frame(frame+b'\x00',size)
    unittest.main()
