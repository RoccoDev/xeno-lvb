EXTENDED_REGISTRY = {}

def get_ext_mapper(magic, xc3):
    global EXTENDED_REGISTRY
    return EXTENDED_REGISTRY.get((magic, xc3))

def register_mappers(mappers, xc3):
    global EXTENDED_REGISTRY

    for magic, mapper in mappers.items():
        EXTENDED_REGISTRY[(magic, xc3)] = mapper