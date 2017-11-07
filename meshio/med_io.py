# -*- coding: utf-8 -*-
#
'''
I/O for MED/Salome, cf.
<http://docs.salome-platform.org/latest/dev/MEDCoupling/med-file.html>.

.. moduleauthor:: Nico Schlömer <nico.schloemer@gmail.com>
'''
import numpy


def read(filename):
    import h5py

    f = h5py.File(filename, 'r')

    # def print_group(grp, indent=0):
    #     for key in grp:
    #         if isinstance(key, int) or \
    #                 isinstance(key, float) or \
    #                 isinstance(key, numpy.int32) or \
    #                 isinstance(key, numpy.int64):
    #             print(indent*' ' + repr(key))
    #         elif isinstance(key, numpy.ndarray):
    #             print(indent*' ' + repr(key))
    #         else:
    #             print(indent*' ' + str(list(grp[key].attrs.items())))
    #             try:
    #                 print(indent*' ' + str(grp[key]))
    #                 print_group(grp[key], indent=indent+4)
    #             except TypeError:
    #                 print(type(key))
    #                 break
    #     return

    # print_group(f)

    # <HDF5 group "/ENS_MAA" (1 members)>
    ens_maa = f['ENS_MAA']
    meshes = ens_maa.keys()
    assert len(meshes) == 1

    mesh = ens_maa[list(meshes)[0]]

    if 'NOE' not in mesh:
        # One needs NOE (node) and MAI (element) data. If they are not
        # available in the mesh, check for the submesh.
        submeshes = mesh.keys()
        assert len(submeshes) == 1
        mesh = mesh[list(submeshes)[0]]

    pts_dataset = mesh['NOE']['COO']
    number = pts_dataset.attrs['NBR']
    points = pts_dataset[()].reshape(-1, number).T
    if points.shape[1] == 2:
        points = numpy.column_stack([points, numpy.zeros(len(points))])

    cells = {}

    mai = mesh['MAI']

    if 'PO1' in mai:
        cells['vertex'] = mai['PO1']['NOD'][()].reshape(1, -1).T - 1

    if 'SE2' in mai:
        cells['line'] = mai['SE2']['NOD'][()].reshape(2, -1).T - 1

    if 'TR3' in mai:
        cells['triangle'] = mai['TR3']['NOD'][()].reshape(3, -1).T - 1

    if 'TE4' in mai:
        cells['tetra'] = mai['TE4']['NOD'][()].reshape(4, -1).T - 1

    if 'HE8' in mai:
        cells['hexahedron'] = mai['HE8']['NOD'][()].reshape(8, -1).T - 1

    if 'QU4' in mai:
        cells['quad'] = mai['QU4']['NOD'][()].reshape(4, -1).T - 1

    return points, cells, {}, {}, {}


def write(
        filename,
        points,
        cells,
        point_data=None,
        cell_data=None,
        field_data=None,
        add_global_ids=True
        ):
    import h5py

    point_data = {} if point_data is None else point_data
    cell_data = {} if cell_data is None else cell_data
    field_data = {} if field_data is None else field_data

    f = h5py.File(filename, 'w')

    # Pretend this is a MED 3.0.6 file
    f.attrs.create('MAJ', 3)
    f.attrs.create('MIN', 0)
    f.attrs.create('REL', 6)

    ens_maa = f.create_group('ENS_MAA')

    mesh_name = 'meshio'
    mesh = ens_maa.create_group(mesh_name)

    # points with tags
    noe_group = mesh.create_group('NOE')
    coo_dataset = noe_group.create_dataset('COO', data=points.T)
    coo_dataset.attrs.create('NBR', len(points))
    tags = numpy.zeros(len(points), dtype=int)
    noe_group.create_dataset('FAM', data=tags)

    # cells with tags
    mai_group = mesh.create_group('MAI')
    if 'triangle' in cells:
        tr3_group = mai_group.create_group('TR3')
        tr3_group.create_dataset('NOD', data=cells['triangle'].T+1)

    if 'tetra' in cells:
        te4_group = mai_group.create_group('TE4')
        te4_group.create_dataset('NOD', data=cells['tetra'].T+1)

    if 'hexahedron' in cells:
        group = mai_group.create_group('HE8')
        group.create_dataset('NOD', data=cells['hexahedron'].T+1)

    if 'quad' in cells:
        group = mai_group.create_group('QU4')
        group.create_dataset('NOD', data=cells['quad'].T+1)

    if 'vertex' in cells:
        group = mai_group.create_group('PO1')
        group.create_dataset('NOD', data=cells['vertex'].T+1)

    if 'line' in cells:
        group = mai_group.create_group('SE2')
        group.create_dataset('NOD', data=cells['line'].T+1)

    return
