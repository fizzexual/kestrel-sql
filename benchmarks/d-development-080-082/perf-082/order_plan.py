"""Six complete permutations; variant rotation uses fixed seed index, not position."""
from collections import Counter
PERMUTATIONS=[(0,1,2),(1,2,0),(2,0,1),(0,2,1),(2,1,0),(1,0,2)]
LABELS=['baseline_a','baseline_b','hybrid'];SIZES=[0,50000,99000]
def plan():
    cases=[]
    for turn,size_order in enumerate(PERMUTATIONS*2):
        for seed_index in size_order:
            seed=SIZES[seed_index]
            for variant_index in PERMUTATIONS[(turn+seed_index)%6]:
                v=LABELS[variant_index]
                cases.append({'round':turn,'seed_receipts':seed,'variant':v,'mode':'hybrid','repetitions':64})
    validate(cases)
    return cases
def validate(cases):
    assert len(cases)==108
    size_slots={s:Counter() for s in SIZES};variant_slots={s:{v:Counter() for v in LABELS} for s in SIZES}
    relative={s:Counter() for s in SIZES};orders={s:[] for s in SIZES}
    for turn in range(12):
        group=[c for c in cases if c['round']==turn];assert len(group)==9
        sizes=[group[i*3]['seed_receipts'] for i in range(3)];assert set(sizes)==set(SIZES)
        for position,seed in enumerate(sizes):
            block=group[position*3:position*3+3]
            assert all(c['seed_receipts']==seed and c['repetitions']==64 for c in block)
            assert all(c['mode']=='hybrid' for c in block)
            variants=[c['variant'] for c in block];assert set(variants)==set(LABELS)
            size_slots[seed][position]+=1;orders[seed].append(tuple(variants))
            for slot,v in enumerate(variants):variant_slots[seed][v][slot]+=1
            relative[seed]['A_before_B' if variants.index('baseline_a')<variants.index('baseline_b') else 'B_before_A']+=1
    for seed in SIZES:
        assert size_slots[seed]=={0:4,1:4,2:4}
        assert len(set(orders[seed]))==6
        assert relative[seed]=={'A_before_B':6,'B_before_A':6}
        for v in LABELS:assert variant_slots[seed][v]=={0:4,1:4,2:4}
    return {'passed':True,'cases':108,'rounds':12,'per_size_all_six_variant_orders':True,
        'each_variant_each_position_per_size':4,'each_size_each_position':4,'each_AB_relative_order':6,
        'size_slot_counts':size_slots,'variant_slot_counts':variant_slots,'relative_AB_counts':relative}

if __name__=='__main__':
    import unittest
    class OrderTests(unittest.TestCase):
        def test_final_plan_balanced(self):self.assertTrue(validate(plan())['passed'])
        def test_old_cancelling_rotation_rejected(self):
            cases=[]
            for turn in range(12):
                order=SIZES[turn%3:]+SIZES[:turn%3]
                for index,seed in enumerate(order):
                    shift=(turn+index)%3
                    cases.extend({'round':turn,'seed_receipts':seed,'variant':v,'mode':'hybrid','repetitions':64} for v in LABELS[shift:]+LABELS[:shift])
            with self.assertRaises(AssertionError):validate(cases)
        def test_duplicate_and_wrong_size_rejected(self):
            for mutation in ['variant','seed']:
                cases=plan()
                if mutation=='variant':cases[1]['variant']=cases[0]['variant']
                else:cases[2]['seed_receipts']=50000
                with self.assertRaises(AssertionError):validate(cases)
    unittest.main()
