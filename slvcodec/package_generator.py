'''
Functions to generate packages from existing packages that define types to
convert the types back and forth to std_logic_vector.
'''


import os
import jinja2

from slvcodec import typs, package, symbolic_math

declarations_template = '''  constant {type.identifier}_width: natural := {width_expression};
  function to_slvcodec (constant data: {type.identifier}) return std_logic_vector;
  function from_slvcodec (constant slv: std_logic_vector) return {type.identifier};'''

unconstrained_declarations_template = '''  function to_slvcodec (constant data: {type.identifier}) return std_logic_vector;
  function from_slvcodec (constant slv: std_logic_vector) return {type.identifier};'''

constrained_declarations_template = '''  constant {type.identifier}_width: natural := {width_expression};'''


def make_record_declarations_and_definitions(record_type):
    '''
    Create declarations and definitions of functions to convert to and from
    record types.
    '''
    declarations = declarations_template.format(
        type=record_type,
        width_expression=symbolic_math.str_expression(record_type.width),
        )
    template_fn = os.path.join(os.path.dirname(__file__), 'templates',
                               'slvcodec_record_template.vhd')
    with open(template_fn, 'r') as f:
        definitions_template = jinja2.Template(f.read())
    indices_names_and_widths = []
    for index, name_and_subtype in enumerate(record_type.names_and_subtypes):
        name, subtype = name_and_subtype
        indices_names_and_widths.append(
            (index, name, symbolic_math.str_expression(subtype.width)))
    definitions = definitions_template.render(
        type=record_type.identifier,
        indices_names_and_widths=indices_names_and_widths)
    return declarations, definitions


def make_array_declarations_and_definitions(array_type):
    '''
    Create declarations and definitions of functions to convert to and from
    array types.
    '''
    if hasattr(array_type, 'size'):
        declarations = constrained_declarations_template.format(
            type=array_type,
            width_expression=symbolic_math.str_expression(array_type.width),
            )
        definitions = ''
    else:
        declarations = unconstrained_declarations_template.format(
            type=array_type
            )
        template_fn = os.path.join(os.path.dirname(__file__), 'templates', 'slvcodec_array_template.vhd')
        with open(template_fn, 'r') as f:
            definitions_template = jinja2.Template(f.read())
        definitions = definitions_template.render(
            type=array_type.identifier,
            subtype=array_type.subtype,
            )
    return declarations, definitions


def make_declarations_and_definitions(typ):
    '''
    Create declarations and definitions of functions to convert to and from
    array and record types.  Other types are not yet supported.
    '''
    if type(typ) in (typs.Array, typs.ConstrainedArray,
                     typs.ConstrainedStdLogicVector):
        return make_array_declarations_and_definitions(typ)
    elif isinstance(typ, typs.Record):
        return make_record_declarations_and_definitions(typ)
    else:
        raise Exception('Unknown typ {}'.format(typ))


def make_slvcodec_package(pkg):
    '''
    Create a package containing functions to convert to and from
    std_logic_vector.  A package is taken as an input, all the types
    are parsed from it and the converting functions generated.
    '''
    all_declarations = []
    all_definitions = []
    for typ in pkg.types.values():
        declarations, definitions = make_declarations_and_definitions(typ)
        all_declarations.append(declarations)
        all_definitions.append(definitions)
    combined_declarations = '\n'.join(all_declarations)
    combined_definitions = '\n'.join(all_definitions)
    use_lines = []
    libraries = []
    for use in pkg.uses.values():
        use_lines.append('use {}.{}.{};'.format(
            use.library, use.design_unit, use.name_within))
        if use.library not in libraries:
            libraries.append(use.library)
    use_lines.append('use ieee.numeric_std.all;'.format(pkg.identifier))
    use_lines.append('use work.{}.all;'.format(pkg.identifier))
    use_lines.append('use work.slvcodec.all;'.format(pkg.identifier))
    library_lines = ['library {};'.format(library) for library in libraries]
    template = """{library_lines}
{use_lines}

package {package_name} is

{declarations}

end package;

package body {package_name} is

{definitions}

end package body;
"""
    slvcodec_pkg = template.format(
        library_lines='\n'.join(library_lines),
        use_lines='\n'.join(use_lines),
        package_name=pkg.identifier+'_slvcodec',
        declarations=combined_declarations,
        definitions=combined_definitions,
        )
    return slvcodec_pkg
