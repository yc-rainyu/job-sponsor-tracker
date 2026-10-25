import pytest

from app.services.sponsors.normalise import normalise_name

# (raw, legal_norm, trading_raw, trading_norm)
CASES = [
    (' AaruvikA Limited', 'aaruvika ltd', None, None),
    ('Asian  African Foods Ltd ', 'asian african foods ltd', None, None),
    ('Stripe Payments UK Ltd', 'stripe payments uk ltd', None, None),
    ('J.P. Morgan Limited', 'jp morgan ltd', None, None),
    ('Marks & Spencer PLC', 'marks and spencer plc', None, None),
    ('Smith & Jones L.L.P.', 'smith and jones llp', None, None),
    ('Barclays Bank Public Limited Company', 'barclays bank plc', None, None),
    ('The Boots Company PLC', 'boots co plc', None, None),
    ('The University of Edinburgh', 'university of edinburgh', None, None),
    ('Roofoods Ltd t/a Deliveroo', 'roofoods ltd', 'Deliveroo', 'deliveroo'),
    ('BRANOS OXFORD LTD T/A LILO', 'branos oxford ltd', 'LILO', 'lilo'),
    ('ABC Limited trading as CoolBrand', 'abc ltd', 'CoolBrand', 'coolbrand'),
    ('Foo Ltd t/as Bar', 'foo ltd', 'Bar', 'bar'),
    (
        'Fresh Foods Ltd t/a Green Grocer, Daily Mart and Farm Shop',
        'fresh foods ltd',
        'Green Grocer, Daily Mart and Farm Shop',
        'green grocer daily mart and farm shop',
    ),
    (
        '  The Foo & Bar Limited T/A BrandX  ',
        'foo and bar ltd',
        'BrandX',
        'brandx',
    ),
]


@pytest.mark.parametrize('raw, legal, trading_raw, trading_norm', CASES)
def test_normalise_name(raw, legal, trading_raw, trading_norm):
    assert normalise_name(raw) == (legal, trading_raw, trading_norm)
