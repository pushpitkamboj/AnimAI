def get_3d_vmob_gradient_start_and_end_points(vmob) -> tuple[Point3D, Point3D]:
    return (
        get_3d_vmob_start_corner(vmob),
        get_3d_vmob_end_corner(vmob),
    )





def get_3d_vmob_start_corner_index(vmob) -> Literal[0]:
    return 0





def get_3d_vmob_end_corner_index(vmob) -> int:
    return ((len(vmob.points) - 1) // 6) * 3





def get_3d_vmob_start_corner(vmob) -> Point3D:
    if vmob.get_num_points() == 0:
        return np.array(ORIGIN)
    return vmob.points[get_3d_vmob_start_corner_index(vmob)]





def get_3d_vmob_end_corner(vmob) -> Point3D:
    if vmob.get_num_points() == 0:
        return np.array(ORIGIN)
    return vmob.points[get_3d_vmob_end_corner_index(vmob)]





def get_3d_vmob_unit_normal(vmob, point_index: int) -> Vector3D:
    n_points = vmob.get_num_points()
    if len(vmob.get_anchors()) <= 2:
        return np.array(UP)
    i = point_index
    im3 = i - 3 if i > 2 else (n_points - 4)
    ip3 = i + 3 if i < (n_points - 3) else 3
    unit_normal = get_unit_normal(
        vmob.points[ip3] - vmob.points[i],
        vmob.points[im3] - vmob.points[i],
    )
    if np.linalg.norm(unit_normal) == 0:
        return np.array(UP)
    return unit_normal





def get_3d_vmob_start_corner_unit_normal(vmob) -> Vector3D:
    return get_3d_vmob_unit_normal(vmob, get_3d_vmob_start_corner_index(vmob))





def get_3d_vmob_end_corner_unit_normal(vmob) -> Vector3D:
    return get_3d_vmob_unit_normal(vmob, get_3d_vmob_end_corner_index(vmob))
