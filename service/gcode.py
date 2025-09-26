import os
import sys
import time
import traceback

# 尝试导入FreeCAD (无头模式，不需要GUI)
try:
    # 设置FreeCAD为无头模式
    import sys
    sys.argv = ['freecad', '-c']  # 控制台模式
    
    import FreeCAD
    import Part
    # 不导入GUI相关模块
    FREECAD_AVAILABLE = True
    print("[INFO] FreeCAD无头模式加载成功")
except ImportError as e:
    print("[WARNING] FreeCAD不可用，G-code转换功能将受限", e)
    FREECAD_AVAILABLE = False


# G-code转换支持的CAD格式
GCODE_SUPPORTED_CAD_FORMATS = {
    '.brep': 'BREP (Boundary Representation)',
    '.bep': 'BREP (Boundary Representation)', 
    '.iges': 'IGES (Initial Graphics Exchange Specification)',
    '.igs': 'IGES (Initial Graphics Exchange Specification)',
    '.step': 'STEP (Standard for Exchange of Product Data)',
    '.stp': 'STEP (Standard for Exchange of Product Data)'
}


def is_cad_file(file_path):
    """
    检查文件是否为支持的CAD格式
    
    参数:
        file_path: 文件路径
        
    返回:
        bool: 是否为支持的CAD文件
    """
    if not os.path.exists(file_path):
        return False
    
    # 支持的CAD文件扩展名
    cad_extensions = set(GCODE_SUPPORTED_CAD_FORMATS.keys())
    
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in cad_extensions


def cad_to_gcode(input_path, output_path=None, **kwargs):
    """
    将CAD文件转换为G-code文件
    
    参数:
        input_path: 输入CAD文件路径
        output_path: 输出G-code文件路径，如果为None则自动生成
        kwargs: 可选参数:
            # 刀具参数
            - tool_diameter: 刀具直径 (mm, 默认3.0)
            - tool_type: 刀具类型 ('end_mill', 'ball_mill', 'drill', 默认'end_mill')
            
            # 切削参数
            - spindle_speed: 主轴转速 (RPM, 默认10000)
            - feed_rate: 进给速度 (mm/min, 默认300)
            - plunge_rate: 下刀速度 (mm/min, 默认100)
            - step_down: 每层切削深度 (mm, 默认1.0)
            - step_over: 步距比例 (0.1-0.8, 默认0.6)
            
            # 加工策略
            - operation_type: 加工类型 ('roughing', 'finishing', 'profile', 默认'profile')
            - cutting_direction: 切削方向 ('climb', 'conventional', 默认'climb')
            
            # 安全参数
            - safe_height: 安全高度 (mm, 默认5.0)
            - clearance_height: 间隙高度 (mm, 默认2.0)
            
            # 材料参数
            - material: 工件材质 ('aluminum', 'steel', 'plastic', 默认'aluminum')
            - surface_finish: 表面粗糙度要求 ('rough', 'medium', 'fine', 默认'medium')
            
            # 冷却参数
            - use_coolant: 是否使用冷却液 (bool, 默认False)
            - coolant_type: 冷却类型 ('flood', 'mist', 默认'flood')
    
    返回:
        tuple: (是否成功, 输出文件路径或错误信息)
    """
    # 检查FreeCAD是否可用
    if not FREECAD_AVAILABLE:
        return False, "FreeCAD未安装或不可用"
    
    # 检查输入文件
    if not os.path.exists(input_path):
        return False, f"输入文件不存在: {input_path}"
    
    # 检查是否为支持的CAD文件
    if not is_cad_file(input_path):
        return False, f"不支持的文件格式: {input_path}"
    
    # 生成输出路径
    if not output_path:
        input_dir = os.path.dirname(input_path)
        input_basename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(input_dir, f"{input_basename}.gcode")
    
    # 提取参数
    tool_diameter = kwargs.get('tool_diameter', 3.0)
    spindle_speed = kwargs.get('spindle_speed', 10000)
    feed_rate = kwargs.get('feed_rate', 300)
    safe_height = kwargs.get('safe_height', 5.0)
    step_down = kwargs.get('step_down', 1.0)
    
    print(f"[INFO] 开始CAD到G-code转换: {input_path} -> {output_path}")
    print(f"[INFO] 参数: 刀具={tool_diameter}mm, 转速={spindle_speed}RPM, 进给={feed_rate}mm/min")
    
    start_time = time.time()
    doc = None
    
    try:
        # 创建FreeCAD文档
        doc = FreeCAD.newDocument("GCodeConversion")
        
        # 根据文件扩展名导入CAD文件
        file_ext = os.path.splitext(input_path)[1].lower()
        
        if file_ext in ['.step', '.stp']:
            print("[INFO] 导入STEP文件...")
            Part.insert(input_path, doc.Name)
        elif file_ext in ['.iges', '.igs']:
            print("[INFO] 导入IGES文件...")
            Part.insert(input_path, doc.Name)
        elif file_ext in ['.brep', '.bep']:
            print("[INFO] 导入BREP文件...")
            Part.insert(input_path, doc.Name)
        else:
            return False, f"暂不支持的文件格式: {file_ext}"
        
        # 检查导入是否成功
        if len(doc.Objects) == 0:
            return False, "导入CAD文件失败，没有创建对象"
        
        print(f"[INFO] 成功导入 {len(doc.Objects)} 个对象")
        
        # 分析CAD几何体并生成G-code
        print("[INFO] 分析CAD几何体...")
        main_object = doc.Objects[0]
        
        # 获取详细的几何信息
        geometry_info = analyze_cad_geometry(main_object)
        
        # 生成基于实际几何体的G-code
        print("[INFO] 生成复杂刀具路径...")
        gcode_content = generate_advanced_gcode(
            geometry_info=geometry_info,
            tool_diameter=tool_diameter,
            spindle_speed=spindle_speed,
            feed_rate=feed_rate,
            plunge_rate=kwargs.get('plunge_rate', 100),
            safe_height=safe_height,
            step_down=step_down,
            step_over=kwargs.get('step_over', 0.6),
            operation_type=kwargs.get('operation_type', 'profile')
        )
        
        # 写入G-code文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(gcode_content)
        
        # 验证输出文件
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path) / 1024.0
            print(f"[INFO] G-code文件生成成功: {output_size:.2f} KB")
            
            end_time = time.time()
            print(f"[SUCCESS] 转换完成! 用时: {end_time - start_time:.2f} 秒")
            return True, output_path
        else:
            return False, "G-code文件生成失败"
            
    except Exception as e:
        error_msg = f"转换失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[DEBUG] 详细错误: {traceback.format_exc()}")
        return False, error_msg
        
    finally:
        # 清理资源
        if doc is not None:
            try:
                FreeCAD.closeDocument(doc.Name)
            except:
                pass


def analyze_cad_geometry(cad_object):
    """
    分析CAD对象的几何特征
    
    参数:
        cad_object: FreeCAD对象
        
    返回:
        dict: 包含几何信息的字典
    """
    geometry_info = {
        'bbox': None,
        'faces': [],
        'edges': [],
        'vertices': [],
        'volume': 0,
        'surface_area': 0,
        'complexity': 'simple'
    }
    
    try:
        if hasattr(cad_object, 'Shape'):
            shape = cad_object.Shape
            
            # 基本信息
            geometry_info['bbox'] = shape.BoundBox
            geometry_info['volume'] = shape.Volume if hasattr(shape, 'Volume') else 0
            geometry_info['surface_area'] = shape.Area if hasattr(shape, 'Area') else 0
            
            print(f"[INFO] 模型边界: X({shape.BoundBox.XMin:.2f}-{shape.BoundBox.XMax:.2f}) "
                  f"Y({shape.BoundBox.YMin:.2f}-{shape.BoundBox.YMax:.2f}) "
                  f"Z({shape.BoundBox.ZMin:.2f}-{shape.BoundBox.ZMax:.2f})")
            print(f"[INFO] 体积: {geometry_info['volume']:.2f} mm³")
            print(f"[INFO] 表面积: {geometry_info['surface_area']:.2f} mm²")
            
            # 分析面
            if hasattr(shape, 'Faces'):
                geometry_info['faces'] = shape.Faces
                face_count = len(shape.Faces)
                print(f"[INFO] 面数量: {face_count}")
                
                # 分析面的类型
                planar_faces = 0
                curved_faces = 0
                
                for face in shape.Faces[:min(10, face_count)]:  # 只分析前10个面避免太慢
                    try:
                        if hasattr(face, 'Surface'):
                            surface_type = str(type(face.Surface)).lower()
                            if 'plane' in surface_type:
                                planar_faces += 1
                            else:
                                curved_faces += 1
                    except:
                        pass
                
                print(f"[INFO] 平面: {planar_faces}, 曲面: {curved_faces}")
                
                # 根据面数量判断复杂度
                if face_count > 100:
                    geometry_info['complexity'] = 'complex'
                elif face_count > 20:
                    geometry_info['complexity'] = 'medium'
                else:
                    geometry_info['complexity'] = 'simple'
            
            # 分析边
            if hasattr(shape, 'Edges'):
                geometry_info['edges'] = shape.Edges
                edge_count = len(shape.Edges)
                print(f"[INFO] 边数量: {edge_count}")
                
                # 分析边的类型
                straight_edges = 0
                curved_edges = 0
                
                for edge in shape.Edges[:min(20, edge_count)]:  # 只分析前20条边
                    try:
                        if hasattr(edge, 'Curve'):
                            curve_type = str(type(edge.Curve)).lower()
                            if 'line' in curve_type:
                                straight_edges += 1
                            else:
                                curved_edges += 1
                    except:
                        pass
                
                print(f"[INFO] 直线边: {straight_edges}, 曲线边: {curved_edges}")
            
            # 分析顶点
            if hasattr(shape, 'Vertexes'):
                geometry_info['vertices'] = shape.Vertexes
                print(f"[INFO] 顶点数量: {len(shape.Vertexes)}")
                
        print(f"[INFO] 几何复杂度: {geometry_info['complexity']}")
        
    except Exception as e:
        print(f"[WARNING] 几何分析失败: {str(e)}")
        # 创建默认的边界框
        if hasattr(cad_object, 'Shape') and hasattr(cad_object.Shape, 'BoundBox'):
            geometry_info['bbox'] = cad_object.Shape.BoundBox
    
    return geometry_info


def generate_advanced_gcode(geometry_info, tool_diameter=3.0, spindle_speed=10000, 
                          feed_rate=300, plunge_rate=100, safe_height=5.0, 
                          step_down=1.0, step_over=0.6, operation_type='profile'):
    """
    基于几何分析生成高级G-code
    
    参数:
        geometry_info: 几何信息字典
        其他参数: 加工参数
        
    返回:
        str: G-code内容
    """
    bbox = geometry_info.get('bbox')
    complexity = geometry_info.get('complexity', 'simple')
    face_count = len(geometry_info.get('faces', []))
    edge_count = len(geometry_info.get('edges', []))
    
    print(f"[INFO] 生成{complexity}复杂度的G-code，面数: {face_count}, 边数: {edge_count}")
    
    gcode_lines = [
        f"; Advanced G-code generated from CAD geometry",
        f"; Complexity: {complexity}",
        f"; Faces: {face_count}, Edges: {edge_count}",
        f"; Tool: Ø{tool_diameter}mm {operation_type}",
        f"; Speed: {spindle_speed}RPM, Feed: {feed_rate}mm/min",
        f"; Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    # 添加边界框信息
    if bbox:
        gcode_lines.extend([
            f"; Model bounds: X({bbox.XMin:.2f} to {bbox.XMax:.2f}) Y({bbox.YMin:.2f} to {bbox.YMax:.2f}) Z({bbox.ZMin:.2f} to {bbox.ZMax:.2f})",
            f"; Model size: {bbox.XLength:.2f} x {bbox.YLength:.2f} x {bbox.ZLength:.2f} mm",
            f"; Volume: {geometry_info.get('volume', 0):.2f} mm³",
            "",
        ])
    
    # G-code初始化
    gcode_lines.extend([
        "; Program initialization",
        "G21 ; Set units to millimeters",
        "G90 ; Absolute positioning",
        "G17 ; XY plane selection", 
        "G94 ; Feed rate per minute",
        "G54 ; Work coordinate system",
        "",
        f"M3 S{spindle_speed} ; Start spindle",
        "G4 P3 ; Wait for spindle to reach speed",
        "",
        f"G0 Z{safe_height} ; Move to safe height",
        "",
    ])
    
    if bbox:
        # 根据复杂度生成不同的刀具路径
        if complexity == 'simple':
            gcode_lines.extend(generate_simple_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, operation_type))
        elif complexity == 'medium':
            gcode_lines.extend(generate_medium_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, step_over, operation_type))
        else:  # complex
            gcode_lines.extend(generate_complex_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, step_over, operation_type))
    else:
        gcode_lines.extend([
            "; No geometry information available - using default path",
            "G0 X0 Y0",
            f"G1 Z-{step_down} F{plunge_rate}",
            f"G1 X10 F{feed_rate}",
        ])
    
    # G-code结束
    gcode_lines.extend([
        "",
        "; Program end",
        f"G0 Z{safe_height} ; Return to safe height",
        "M5 ; Stop spindle",
        "G0 X0 Y0 ; Return to origin",
        "M30 ; Program end and rewind",
        ""
    ])
    
    return '\n'.join(gcode_lines)


def generate_simple_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, operation_type):
    """生成简单零件的刀具路径"""
    tool_radius = tool_diameter / 2
    x_min = bbox.XMin - tool_radius
    x_max = bbox.XMax + tool_radius
    y_min = bbox.YMin - tool_radius
    y_max = bbox.YMax + tool_radius
    z_top = bbox.ZMax
    
    lines = [
        f"; Simple {operation_type} toolpath",
        f"G0 X{x_min:.3f} Y{y_min:.3f} ; Move to start",
        f"G1 Z{z_top - step_down:.3f} F{plunge_rate} ; Plunge",
        f"G1 X{x_max:.3f} F{feed_rate} ; Cut X+",
        f"G1 Y{y_max:.3f} ; Cut Y+",
        f"G1 X{x_min:.3f} ; Cut X-",
        f"G1 Y{y_min:.3f} ; Cut Y- (complete rectangle)",
    ]
    return lines


def generate_medium_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, step_over, operation_type):
    """生成中等复杂度零件的刀具路径"""
    tool_radius = tool_diameter / 2
    x_min = bbox.XMin - tool_radius
    x_max = bbox.XMax + tool_radius
    y_min = bbox.YMin - tool_radius
    y_max = bbox.YMax + tool_radius
    z_top = bbox.ZMax
    
    stepover_distance = tool_diameter * step_over
    
    lines = [
        f"; Medium complexity {operation_type} toolpath",
        f"; Step over: {stepover_distance:.3f}mm ({step_over*100:.0f}% of tool diameter)",
    ]
    
    if operation_type == 'profile':
        # 轮廓加工 - 多层外轮廓
        current_z = z_top
        layer = 1
        while current_z > bbox.ZMin:
            current_z = max(current_z - step_down, bbox.ZMin)
            lines.extend([
                f"",
                f"; Layer {layer} at Z{current_z:.3f}",
                f"G0 X{x_min:.3f} Y{y_min:.3f}",
                f"G1 Z{current_z:.3f} F{plunge_rate}",
                f"G1 X{x_max:.3f} F{feed_rate}",
                f"G1 Y{y_max:.3f}",
                f"G1 X{x_min:.3f}",
                f"G1 Y{y_min:.3f}",
            ])
            layer += 1
    else:
        # 型腔加工 - 来回切削
        y_current = y_min
        direction = 1
        layer = 1
        
        current_z = z_top - step_down
        lines.extend([
            f"",
            f"; Pocket roughing at Z{current_z:.3f}",
            f"G0 X{x_min:.3f} Y{y_min:.3f}",
            f"G1 Z{current_z:.3f} F{plunge_rate}",
        ])
        
        while y_current <= y_max:
            if direction > 0:
                lines.append(f"G1 X{x_max:.3f} F{feed_rate} ; Cut right")
            else:
                lines.append(f"G1 X{x_min:.3f} F{feed_rate} ; Cut left")
            
            y_current += stepover_distance
            if y_current <= y_max:
                lines.append(f"G1 Y{y_current:.3f} ; Step over")
            
            direction *= -1
    
    return lines


def generate_complex_toolpath(bbox, tool_diameter, feed_rate, plunge_rate, step_down, step_over, operation_type):
    """生成复杂零件的刀具路径"""
    tool_radius = tool_diameter / 2
    x_min = bbox.XMin - tool_radius
    x_max = bbox.XMax + tool_radius
    y_min = bbox.YMin - tool_radius
    y_max = bbox.YMax + tool_radius
    z_top = bbox.ZMax
    
    stepover_distance = tool_diameter * step_over
    
    lines = [
        f"; Complex {operation_type} toolpath",
        f"; Multiple strategies for optimal material removal",
    ]
    
    # 复杂零件使用多种策略
    current_z = z_top
    layer = 1
    
    # 第一层：粗加工（大步距）
    rough_stepover = tool_diameter * 0.8
    current_z = z_top - step_down
    
    lines.extend([
        f"",
        f"; === ROUGHING PASS ===",
        f"; Layer {layer} roughing at Z{current_z:.3f}",
        f"G0 X{x_min:.3f} Y{y_min:.3f}",
        f"G1 Z{current_z:.3f} F{plunge_rate}",
    ])
    
    # 螺旋进入
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    spiral_radius = tool_diameter
    
    lines.extend([
        f"; Spiral entry",
        f"G0 X{center_x:.3f} Y{center_y:.3f}",
        f"G1 Z{current_z:.3f} F{plunge_rate}",
    ])
    
    # 生成螺旋路径
    import math
    for angle in range(0, 720, 30):  # 2圈，每30度一个点
        rad = math.radians(angle)
        radius = spiral_radius * (1 + angle / 720)
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)
        lines.append(f"G1 X{x:.3f} Y{y:.3f} F{feed_rate}")
    
    # 来回切削清理
    y_current = y_min + rough_stepover
    direction = 1
    
    while y_current <= y_max - rough_stepover:
        if direction > 0:
            lines.extend([
                f"G1 X{x_min + tool_radius:.3f} Y{y_current:.3f}",
                f"G1 X{x_max - tool_radius:.3f} F{feed_rate}"
            ])
        else:
            lines.extend([
                f"G1 X{x_max - tool_radius:.3f} Y{y_current:.3f}",
                f"G1 X{x_min + tool_radius:.3f} F{feed_rate}"
            ])
        
        y_current += rough_stepover
        direction *= -1
    
    # 第二层：半精加工
    if bbox.ZLength > step_down:
        current_z = max(current_z - step_down, bbox.ZMin)
        layer += 1
        
        lines.extend([
            f"",
            f"; === SEMI-FINISHING PASS ===",
            f"; Layer {layer} semi-finishing at Z{current_z:.3f}",
            f"G0 X{x_min:.3f} Y{y_min:.3f}",
            f"G1 Z{current_z:.3f} F{plunge_rate}",
        ])
        
        # 更密集的切削
        y_current = y_min
        direction = 1
        
        while y_current <= y_max:
            if direction > 0:
                lines.append(f"G1 X{x_max:.3f} F{feed_rate*0.8} ; Semi-finish right")
            else:
                lines.append(f"G1 X{x_min:.3f} F{feed_rate*0.8} ; Semi-finish left")
            
            y_current += stepover_distance
            if y_current <= y_max:
                lines.append(f"G1 Y{y_current:.3f}")
            
            direction *= -1
    
    # 精加工轮廓
    lines.extend([
        f"",
        f"; === FINISHING PASS ===",
        f"; Final contour at Z{current_z:.3f}",
        f"G0 X{x_min:.3f} Y{y_min:.3f}",
        f"G1 X{x_max:.3f} F{feed_rate*0.6} ; Finish contour",
        f"G1 Y{y_max:.3f}",
        f"G1 X{x_min:.3f}",
        f"G1 Y{y_min:.3f}",
    ])
    
    return lines


def generate_gcode_from_geometry(bbox=None, tool_diameter=3.0, spindle_speed=10000, 
                               feed_rate=300, safe_height=5.0, step_down=1.0):
    """
    基于CAD几何体生成G-code
    
    参数:
        bbox: 边界框对象
        tool_diameter: 刀具直径 (mm)
        spindle_speed: 主轴转速 (RPM)
        feed_rate: 进给速度 (mm/min)
        safe_height: 安全高度 (mm)
        step_down: 切削深度 (mm)
    
    返回:
        str: G-code内容
    """
    gcode_lines = [
        f"; G-code generated from CAD file",
        f"; Tool diameter: {tool_diameter}mm",
        f"; Spindle speed: {spindle_speed}RPM",
        f"; Feed rate: {feed_rate}mm/min",
        f"; Safe height: {safe_height}mm",
        f"; Step down: {step_down}mm",
        f"; Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    # 添加边界框信息
    if bbox:
        gcode_lines.extend([
            f"; Model bounds: X({bbox.XMin:.2f} to {bbox.XMax:.2f}) Y({bbox.YMin:.2f} to {bbox.YMax:.2f}) Z({bbox.ZMin:.2f} to {bbox.ZMax:.2f})",
            f"; Model size: {bbox.XLength:.2f} x {bbox.YLength:.2f} x {bbox.ZLength:.2f} mm",
            "",
        ])
    
    gcode_lines.extend([
        "; Program start",
        "G21 ; Set units to millimeters",
        "G90 ; Absolute positioning",
        "G17 ; XY plane selection", 
        "G94 ; Feed rate per minute",
        "G54 ; Work coordinate system",
        "",
        f"M3 S{spindle_speed} ; Start spindle at {spindle_speed} RPM",
        "G4 P2 ; Wait 2 seconds for spindle to reach speed",
        "",
        f"G0 Z{safe_height} ; Move to safe height",
        "",
    ])
    
    # 根据边界框生成简单的轮廓路径
    if bbox:
        # 计算加工区域（考虑刀具半径）
        tool_radius = tool_diameter / 2
        x_min = bbox.XMin - tool_radius
        x_max = bbox.XMax + tool_radius
        y_min = bbox.YMin - tool_radius
        y_max = bbox.YMax + tool_radius
        z_top = bbox.ZMax
        
        gcode_lines.extend([
            f"; Machining area based on model bounds",
            f"; X: {x_min:.2f} to {x_max:.2f}",
            f"; Y: {y_min:.2f} to {y_max:.2f}",
            f"; Tool radius compensation: {tool_radius:.2f}mm",
            "",
            "; Rectangular profile cut around model",
            f"G0 X{x_min:.2f} Y{y_min:.2f} ; Move to start position",
            f"G1 Z{z_top - step_down:.2f} F{feed_rate/2} ; Plunge to cutting depth",
            f"G1 X{x_max:.2f} Y{y_min:.2f} F{feed_rate} ; Cut to X max",
            f"G1 X{x_max:.2f} Y{y_max:.2f} F{feed_rate} ; Cut to Y max", 
            f"G1 X{x_min:.2f} Y{y_max:.2f} F{feed_rate} ; Cut to X min",
            f"G1 X{x_min:.2f} Y{y_min:.2f} F{feed_rate} ; Cut back to start",
        ])
    else:
        # 默认路径（如果没有边界框信息）
        gcode_lines.extend([
            "; Default toolpath (no geometry information available)",
            f"G0 X0 Y0 ; Move to origin",
            f"G1 Z-{step_down} F{feed_rate/2} ; Plunge to cutting depth",
            f"G1 X10 Y0 F{feed_rate} ; Cut line",
            f"G1 X10 Y10 F{feed_rate} ; Cut line",
            f"G1 X0 Y10 F{feed_rate} ; Cut line", 
            f"G1 X0 Y0 F{feed_rate} ; Cut line",
        ])
    
    gcode_lines.extend([
        "",
        "; Program end",
        f"G0 Z{safe_height} ; Return to safe height",
        "M5 ; Stop spindle",
        "G0 X0 Y0 ; Return to origin",
        "M30 ; Program end and rewind"
    ])
    
    return '\n'.join(gcode_lines)


def get_machining_presets():
    """
    获取预设的加工配置
    
    返回:
        dict: 各种材料和加工类型的预设参数
    """
    presets = {
        # 铝合金加工预设
        'aluminum': {
            'profile': {
                'tool_diameter': 3.0,
                'tool_type': 'end_mill',
                'spindle_speed': 12000,
                'feed_rate': 350,
                'plunge_rate': 150,
                'step_down': 1.5,
                'step_over': 0.6,
                'operation_type': 'profile',
                'use_coolant': True,
                'description': '铝合金轮廓加工 - 平衡速度和精度'
            },
            'roughing': {
                'tool_diameter': 6.0,
                'tool_type': 'end_mill',
                'spindle_speed': 8000,
                'feed_rate': 400,
                'plunge_rate': 200,
                'step_down': 2.0,
                'step_over': 0.7,
                'operation_type': 'roughing',
                'use_coolant': True,
                'description': '铝合金粗加工 - 快速去除材料'
            },
            'finishing': {
                'tool_diameter': 2.0,
                'tool_type': 'end_mill',
                'spindle_speed': 15000,
                'feed_rate': 200,
                'plunge_rate': 100,
                'step_down': 0.3,
                'step_over': 0.2,
                'operation_type': 'finishing',
                'use_coolant': True,
                'description': '铝合金精加工 - 获得光滑表面'
            }
        },
        
        # 钢材加工预设
        'steel': {
            'profile': {
                'tool_diameter': 4.0,
                'tool_type': 'end_mill',
                'spindle_speed': 4500,
                'feed_rate': 120,
                'plunge_rate': 40,
                'step_down': 0.8,
                'step_over': 0.5,
                'operation_type': 'profile',
                'use_coolant': True,
                'description': '钢材轮廓加工 - 稳定切削'
            },
            'roughing': {
                'tool_diameter': 8.0,
                'tool_type': 'end_mill',
                'spindle_speed': 3000,
                'feed_rate': 150,
                'plunge_rate': 50,
                'step_down': 0.5,
                'step_over': 0.5,
                'operation_type': 'roughing',
                'use_coolant': True,
                'description': '钢材粗加工 - 保守参数'
            },
            'finishing': {
                'tool_diameter': 3.0,
                'tool_type': 'end_mill',
                'spindle_speed': 6000,
                'feed_rate': 100,
                'plunge_rate': 30,
                'step_down': 0.2,
                'step_over': 0.3,
                'operation_type': 'finishing',
                'use_coolant': True,
                'description': '钢材精加工 - 高精度'
            }
        },
        
        # 塑料加工预设
        'plastic': {
            'profile': {
                'tool_diameter': 4.0,
                'tool_type': 'end_mill',
                'spindle_speed': 12000,
                'feed_rate': 600,
                'plunge_rate': 300,
                'step_down': 3.0,
                'step_over': 0.8,
                'operation_type': 'profile',
                'use_coolant': False,
                'description': '塑料轮廓加工 - 高速切削'
            },
            'roughing': {
                'tool_diameter': 6.0,
                'tool_type': 'end_mill',
                'spindle_speed': 10000,
                'feed_rate': 800,
                'plunge_rate': 400,
                'step_down': 4.0,
                'step_over': 0.8,
                'operation_type': 'roughing',
                'use_coolant': False,
                'description': '塑料粗加工 - 快速去料'
            },
            'finishing': {
                'tool_diameter': 2.0,
                'tool_type': 'end_mill',
                'spindle_speed': 15000,
                'feed_rate': 400,
                'plunge_rate': 200,
                'step_down': 1.0,
                'step_over': 0.3,
                'operation_type': 'finishing',
                'use_coolant': False,
                'description': '塑料精加工 - 光滑表面'
            }
        },
        
        # 3D轮廓加工（复杂曲面）
        '3d_profiling': {
            'ball_mill': {
                'tool_diameter': 1.0,
                'tool_type': 'ball_mill',
                'spindle_speed': 18000,
                'feed_rate': 100,
                'plunge_rate': 50,
                'step_down': 0.1,
                'step_over': 0.1,
                'operation_type': 'finishing',
                'use_coolant': True,
                'description': '3D曲面精加工 - 球头铣刀'
            }
        }
    }
    
    return presets


def get_recommended_tools(material, complexity='medium'):
    """
    根据材料和复杂度推荐刀具配置
    
    参数:
        material: 材料类型 ('aluminum', 'steel', 'plastic')
        complexity: 复杂度 ('simple', 'medium', 'complex')
    
    返回:
        list: 推荐的刀具配置列表
    """
    tool_configs = {
        'aluminum': {
            'simple': [
                {'name': '粗加工', 'diameter': 6.0, 'type': 'end_mill', 'description': '快速去料'},
                {'name': '精加工', 'diameter': 3.0, 'type': 'end_mill', 'description': '表面光洁'}
            ],
            'medium': [
                {'name': '粗加工', 'diameter': 8.0, 'type': 'end_mill', 'description': '大刀快速粗加工'},
                {'name': '半精加工', 'diameter': 4.0, 'type': 'end_mill', 'description': '中等精度'},
                {'name': '精加工', 'diameter': 2.0, 'type': 'end_mill', 'description': '高精度表面'}
            ],
            'complex': [
                {'name': '粗加工', 'diameter': 6.0, 'type': 'end_mill', 'description': '去除大部分材料'},
                {'name': '半精加工', 'diameter': 3.0, 'type': 'end_mill', 'description': '轮廓近似'},
                {'name': '精加工', 'diameter': 1.5, 'type': 'end_mill', 'description': '细节加工'},
                {'name': '3D精加工', 'diameter': 0.5, 'type': 'ball_mill', 'description': '复杂曲面'}
            ]
        },
        'steel': {
            'simple': [
                {'name': '粗加工', 'diameter': 8.0, 'type': 'end_mill', 'description': '保守参数粗加工'},
                {'name': '精加工', 'diameter': 4.0, 'type': 'end_mill', 'description': '精密表面'}
            ],
            'medium': [
                {'name': '粗加工', 'diameter': 10.0, 'type': 'end_mill', 'description': '重型粗加工'},
                {'name': '半精加工', 'diameter': 6.0, 'type': 'end_mill', 'description': '中等切削'},
                {'name': '精加工', 'diameter': 3.0, 'type': 'end_mill', 'description': '最终表面'}
            ]
        },
        'plastic': {
            'simple': [
                {'name': '通用加工', 'diameter': 6.0, 'type': 'end_mill', 'description': '一刀加工完成'}
            ],
            'medium': [
                {'name': '粗加工', 'diameter': 8.0, 'type': 'end_mill', 'description': '快速成型'},
                {'name': '精加工', 'diameter': 4.0, 'type': 'end_mill', 'description': '表面处理'}
            ]
        }
    }
    
    return tool_configs.get(material, {}).get(complexity, [])


# 使用示例
if __name__ == "__main__":
    # 显示可用的预设配置
    print("=== 可用的加工预设配置 ===")
    presets = get_machining_presets()
    for material, operations in presets.items():
        print(f"\n{material.upper()}材料:")
        for operation, params in operations.items():
            print(f"  {operation}: {params['description']}")
            print(f"    刀具: Ø{params['tool_diameter']}mm {params['tool_type']}")
            print(f"    转速: {params['spindle_speed']}RPM, 进给: {params['feed_rate']}mm/min")
    
    # 显示推荐刀具配置
    print("\n=== 推荐刀具配置 ===")
    for material in ['aluminum', 'steel', 'plastic']:
        for complexity in ['simple', 'medium', 'complex']:
            tools = get_recommended_tools(material, complexity)
            if tools:
                print(f"\n{material.upper()} - {complexity}复杂度:")
                for i, tool in enumerate(tools, 1):
                    print(f"  第{i}把刀: {tool['name']} - Ø{tool['diameter']}mm {tool['type']}")
                    print(f"           {tool['description']}")
    
    # 测试文件转换
    print("\n=== 开始测试转换 ===")
    test_file = "C:\\Users\\13016\\Downloads\\Bladev2.step" # 替换为您的测试文件路径
    
    if os.path.exists(test_file):
        print(f"测试文件: {test_file}")
        
        # 使用铝合金精加工预设
        aluminum_finishing = presets['aluminum']['finishing']
        print(f"\n使用预设: 铝合金精加工")
        print(f"参数: {aluminum_finishing['description']}")
        
        success, result = cad_to_gcode(
            test_file,
            **aluminum_finishing  # 使用预设参数
        )
        
        if success:
            print(f"转换成功! 输出文件: {result}")
        else:
            print(f"转换失败: {result}")
    else:
        print(f"测试文件不存在: {test_file}")
        print("请将CAD文件路径替换为实际文件进行测试")
        
        # 演示如何使用预设参数
        print("\n使用示例:")
        print("# 获取预设参数")
        print("presets = get_machining_presets()")
        print("aluminum_roughing = presets['aluminum']['roughing']")
        print("")
        print("# 使用预设参数转换")
        print("success, result = cad_to_gcode('model.step', **aluminum_roughing)")
        print("")
        print("# 或者自定义参数")
        print("success, result = cad_to_gcode(")
        print("    'model.step',")
        print("    tool_diameter=3.0,")
        print("    material='aluminum',")
        print("    operation_type='finishing',")
        print("    spindle_speed=15000")
        print(")")
