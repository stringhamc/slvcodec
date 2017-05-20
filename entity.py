from vunit import vhdl_parser

from slvcodec import package, typ_parser


def parsed_entity_from_filename(filename):
    with open(filename, 'r') as f:
        code = f.read()
        parsed = vhdl_parser.VHDLParser.parse(code, None)
        return parsed


def process_parsed_entity(parsed_entity):
    p_generics = parsed_entity.entities[0].generics
    generics = [Generic(
        name=g.identifier,
        typ=typ_parser.process_subtype_indication(g.subtype_indication),
        ) for g in p_generics]
    p_ports = parsed_entity.entities[0].ports
    ports = [Port(
        name=p.identifier,
        direction=p.mode,
        typ=typ_parser.process_subtype_indication(p.subtype_indication),
        ) for p in p_ports]
    gd = dict([(g.name, g) for g in generics])
    pd = dict([(p.name, p) for p in ports])
    uses = package.get_parsed_package_dependencies(parsed_entity)
    p = UnresolvedEntity(
        identifier=parsed_entity.entities[0].identifier,
        generics=gd,
        ports=pd,
        uses=uses,
    )
    return p


class Generic:

    def __init__(self, name, typ, default=None):
        self.name = name
        self.typ = typ
        self.default = default

    def str_expression(self):
        return self.name


class Port:

    def __init__(self, name, direction, typ):
        self.name = name
        self.direction = direction
        self.typ = typ


class UnresolvedEntity:

    def __init__(self, identifier, generics, ports, uses):
        self.identifier = identifier
        self.generics = generics
        self.ports = ports
        self.uses = uses

    def resolve(self, packages):
        resolved_uses = package.resolve_uses(self.uses, packages)
        available_types, available_constants = package.combine_packages(
            [u.package for u in resolved_uses.values()])
        available_constants = package.exclusive_dict_merge(
            available_constants, self.generics)
        resolved_ports = {}
        for name, port in self.ports.items():
            if port.typ in available_types:
                resolved_typ = available_types[port.typ]
            elif isinstance(port.typ, str):
                raise Exception('Cannot resolve port typ {}'.format(port.typ))
            else:
                resolved_typ = port.typ.resolve(available_types, available_constants)
            resolved_port = Port(name=port.name, direction=port.direction,
                                 typ=resolved_typ)
            resolved_ports[name] = resolved_port
        e = Entity(
            identifier=self.identifier,
            generics=self.generics,
            ports=resolved_ports,
            uses=resolved_uses,
        )
        return e


class Entity(object):

    resolved = True

    def __init__(self, identifier, generics, ports, uses):
        self.identifier = identifier
        self.generics = generics
        self.ports = ports
        self.uses = uses

    def __str__(self):
        return 'Entity({})'.format(self.identifier)

    def __repr__(self):
        return str(self)


def test_dummy_width():

    parsed_entity = parsed_entity_from_filename('tests/dummy.vhd')
    entity = process_parsed_entity(parsed_entity)
    packages = package.process_packages(['tests/vhdl_type_pkg.vhd'])
    resolved_entity = entity.resolve(packages=packages)
    o_data = resolved_entity.ports['o_data']
    i_dummy = resolved_entity.ports['i_dummy']
    assert(o_data.typ.width.value() == 24)
    assert(i_dummy.typ.width.value() == 11)


if __name__ == '__main__':
    test_dummy_width()
