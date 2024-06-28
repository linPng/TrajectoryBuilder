import osmnx as ox
import networkx as nx
import random
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, LinearRing
from shapely.validation import explain_validity
from utils.coordinate_conversion import bd09_to_wgs84
from geopy.distance import geodesic

def parse_fence(fence_str):
    # 解析围栏字符串，返回坐标列表
    points = fence_str.strip(';').split(';')
    coordinates = []
    for point in points:
        lon, lat = map(float, point.split(','))
        coordinates.append((lon, lat))
    return coordinates


def convert_fence_to_wgs84(fence_coords):
    # 将围栏坐标转换为WGS84坐标系
    return [bd09_to_wgs84(lon, lat) for lon, lat in fence_coords]


def fix_polygon(polygon):
    # 修复无效的多边形
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    return polygon


def get_roads_within_fence(fence_coords, buffer_distance=0.005):
    # 获取围栏内的道路网络
    polygon = Polygon(fence_coords)
    if not polygon.is_valid:
        #print(f"Invalid polygon: {explain_validity(polygon)}. Attempting to fix...")
        polygon = fix_polygon(polygon)

    buffered_polygon = polygon.buffer(buffer_distance)
    #print(f"Polygon bounds: {buffered_polygon.bounds}")

    try:
        G = ox.graph_from_polygon(buffered_polygon, network_type='drive', simplify=True)
        print(f"nodes: {len(G.nodes)}")
        if len(G.nodes) == 0:
            raise ValueError("生成的图形没有节点")
    except Exception as e:
        print(f"使用polygon生成图形时出错: {e}")
        raise ValueError("生成的图形没有节点")

    return G


def midpoint(p1, p2):
    """计算两点的中点"""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def find_valid_nearest_point(n_point, m_points, polygon):
    """在m点前后范围内找到距离n点最近且中点在围栏内的点"""
    nearest_point = None
    min_distance = float('inf')
    for point in m_points:
        mid = midpoint(n_point, point)
        if polygon.contains(Point(mid)):
            distance = ((n_point[0] - point[0]) ** 2 + (n_point[1] - point[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
    return nearest_point


def approximate_medial_axis(fence_coords, polygon):
    """
    通过计算每对点的中点来近似计算围栏的中线，并确保中点在围栏内
    """
    n = len(fence_coords)
    midpoints = []
    i, j = 0, n - 1
    while i < j:
        mid = None  # 初始化 mid 以避免未定义
        try:
            range_start = max(0, j - 3)
            range_end = min(n, j + 4)
            range_to_check = fence_coords[range_start:range_end]
            nearest_point = find_valid_nearest_point(fence_coords[i], range_to_check, polygon)
            if nearest_point:
                j = fence_coords.index(nearest_point)
                mid = midpoint(fence_coords[i], fence_coords[j])
            if mid and polygon.contains(Point(mid)):
                midpoints.append(mid)
                i += 1
                j -= 1
            else:
                # 如果找不到合适的点，则直接跳过当前点
                i += 1
                j -= 1
        except Exception as e:
            print(f"Error during midpoint calculation: {e}")
            i += 1
            j -= 1
    if n % 2 == 1:  # 如果围栏点的数量是奇数，添加中间的那个点
        midpoints.append(fence_coords[n // 2])
    return LineString(midpoints)



def generate_route(G, min_distance=10):
    # 生成围栏内的路径
    nodes = list(G.nodes)
    longest_route = []

    for _ in range(10):  # 尝试生成10次，以找到最长路径
        start_node = random.choice(nodes)
        end_node = random.choice(nodes)
        if start_node != end_node:
            try:
                route = nx.shortest_path(G, start_node, end_node, weight='length')
                length = sum(ox.utils_graph.get_route_edge_attributes(G, route, 'length'))
                if length > min_distance and len(route) > len(longest_route):
                    longest_route = route
            except nx.NetworkXNoPath:
                continue

    if not longest_route:
        raise ValueError("无法在围栏内生成有效路径")

    route_coords = [(G.nodes[node]['x'], G.nodes[node]['y']) for node in longest_route]
    return route_coords


def generate_vehicle_trajectory(fence, num_points=100, total_distance=50000, error_margin=0.00003, min_route_distance=10):
    # 生成车辆轨迹
    fence_coords = parse_fence(fence)
    fence_coords_wgs84 = [bd09_to_wgs84(lon, lat) for lon, lat in fence_coords]
    polygon = Polygon(fence_coords_wgs84)

    try:
        G = get_roads_within_fence(fence_coords_wgs84, buffer_distance=0.000001)
        route_coords = generate_route(G, min_route_distance)
        route_line = LineString(route_coords)
    except Exception as e:
        print(f"无法生成道路网络或路径: {e}")
        print("使用围栏轮廓作为路径")
        route_line = approximate_medial_axis(fence_coords_wgs84, polygon)

    #print("route_line==" + str(route_line))

    # 计算路径的总长度 distance_in_meters=distance_in_degrees×111,320
    total_length = route_line.length
    total_distance = total_distance/111320
    # 计算路径的总长度（使用地理距离）
    # 判断是否超过距离
    #print("total_length==" + str(total_length))
    #print("total_distance==" + str(total_distance))
    #print("total_length > total_distance==" + str(total_length > total_distance))

    #处理路径
    sub_line_coords = []
    current_length = 0
    forward = True
    # 随机反向
    if random.choice([True, False]):
        forward = not forward
    #print(f"forward: {forward}")
    # 获取路径中的点的总数
    num_points_in_route = len(route_line.coords)
    #print(f"Total number of points in the route: {num_points_in_route}")
    # 获取路径中的一个随机点
    random_index = random.randint(0, num_points_in_route - 1)
    random_point = route_line.coords[random_index]
    current_index = random_index
    #print(f"Random point from the route: {random_point}")
    while current_length < total_distance:
        if forward:
            next_index = current_index + 1
        else:
            next_index = current_index - 1

        if 0 <= next_index < num_points_in_route:
            next_point = route_line.coords[next_index]
            segment_length = ((random_point[0] - next_point[0]) ** 2 + (random_point[1] - next_point[1]) ** 2) ** 0.5
            if current_length + segment_length > total_distance:
                break
            sub_line_coords.append(next_point)
            current_length += segment_length
            random_point = next_point
            current_index = next_index
        else:
            forward = not forward  # 如果到达路径的尽头，则掉头

    route_line = LineString(sub_line_coords)

    # trajectory_points = [f"{lon},{lat}" for lon, lat in route_line.coords]
    # trajectory_str = ";".join(trajectory_points) + ";"
    # return trajectory_str

    # 计算每两个点之间的间隔距离
    interval = total_distance / num_points if num_points != 0 else 0
    #print("interval==" + str(interval))
    points = []

    for i in range(num_points):
        # 在路径上均匀分布点
        point = route_line.interpolate(interval * i)
        # 添加随机偏移
        for attempt in range(10):  # 最多尝试10次
            offset_x = random.uniform(-error_margin, error_margin)
            offset_y = random.uniform(-error_margin, error_margin)
            point_with_offset = Point(point.x + offset_x, point.y + offset_y)
            if polygon.contains(point_with_offset):
                points.append(point_with_offset)
                break
        else:
            # 如果超过10次仍未成功，跳过该点
            #points.append(point)
            pass

    #随机反向
    if random.choice([True, False]):
        points.reverse()
    # 确保路径点在围栏内
    valid_route_coords = [(point.x, point.y) for point in points]

    trajectory_points = [f"{lon},{lat}" for lon, lat in valid_route_coords]
    trajectory_str = ";".join(trajectory_points) + ";"

    return trajectory_str
