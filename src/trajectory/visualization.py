import folium
from shapely.geometry import Polygon, Point, LineString
from src.utils.coordinate_conversion import bd09_to_wgs84, gcj02_to_wgs84  # 确保这个函数已经在coordinate_conversion.py中定义

def plot_fence_and_trajectory_on_map(fence, trajectory, map_file="map.html", coord_system="bd09"):
    """
    在地图上绘制围栏和轨迹。

    :param fence: 围栏字符串
    :param trajectory: 轨迹字符串
    :param map_file: 地图文件名
    :param coord_system: 坐标系统，可以是 "gcj02" 或 "wgs84"
    """

    print(trajectory)
    # 解析围栏和轨迹
    fence_coords = [(float(lon), float(lat)) for lon, lat in
                    (point.split(',') for point in fence.strip(';').split(';'))]
    trajectory_coords = [(float(lon), float(lat)) for lon, lat in
                         (point.split(',') for point in trajectory.strip(';').split(';'))]
    print(trajectory_coords)
    # 如果是高德坐标系，转换为WGS84
    if coord_system.lower() == "gcj02":
        fence_coords = [gcj02_to_wgs84(lon, lat) for lon, lat in fence_coords]
        # trajectory_coords = [gcj02_to_wgs84(lon, lat) for lon, lat in trajectory_coords]
    if coord_system.lower() == "bd09":
        fence_coords = [bd09_to_wgs84(lon, lat) for lon, lat in fence_coords]

    # 创建地图
    center_point = fence_coords[0]
    m = folium.Map(location=[center_point[1], center_point[0]], zoom_start=14)

    # 绘制围栏
    folium.PolyLine(locations=[(lat, lon) for lon, lat in fence_coords], color='red', weight=2.5, opacity=1).add_to(m)

    # 绘制轨迹
    folium.PolyLine(locations=[(lat, lon) for lon, lat in trajectory_coords], color='blue', weight=2.5, opacity=1).add_to(m)

    # 添加轨迹点标记，并按顺序标记点的序号
    for i, (lon, lat) in enumerate(trajectory_coords):
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(7, 20),
                html=f'<div style="font-size: 12pt; color : black">{i+1}</div>',
            )
        ).add_to(m)

    # 保存地图到文件
    m.save(map_file)
