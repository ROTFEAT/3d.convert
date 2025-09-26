import sys
from api.service.converters.base import BaseConverter
import os
import time
import traceback

# 使用FreeCAD库进行转换
try:
    import FreeCAD
    import Part
except ImportError:
    print("[ERROR] 无法导入FreeCAD模块。请确保FreeCAD已安装并且环境变量正确设置。")
    sys.exit(1)

class STEPToBRPConverter(BaseConverter):
    """将STEP文件转换为BRP文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STEP文件转换为BRP文件
        
        参数:
            input_path: STEP文件路径
            output_path: 输出BRP文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - precision: 转换精度 (默认为0.01)
                   - include_metadata: 是否包含元数据 (默认为True)
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.brp")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        # 提取参数
        precision = kwargs.get('precision', 0.01)
        include_metadata = kwargs.get('include_metadata', True)
        
        print(f"[INFO] 开始STEP到BRP转换: {input_path} -> {output_path}")
        print(f"[INFO] 使用参数: precision={precision}, include_metadata={include_metadata}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
                
            # 使用FreeCAD加载STEP文件
            print("[INFO] 正在加载STEP文件...")
            
            # 创建FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 导入STEP文件
            Part.insert(input_path, doc.Name)
            print("[INFO] 导入STEP文件成功")
            
            # 确保导入成功
            if len(doc.Objects) == 0:
                print("[ERROR] 导入CAD文件后没有对象")
                return False, None
            
            print(f"[INFO] 成功导入 {len(doc.Objects)} 个对象")
            
            # 转换处理
            print("[INFO] 开始处理STEP对象并转换为BRP格式...")
            
            # 收集所有形状对象
            shapes = []
            for obj in doc.Objects:
                if hasattr(obj, "Shape"):
                    shapes.append(obj.Shape)
                    print(f"[INFO] 处理形状: {obj.Name}, 面数: {len(obj.Shape.Faces)}")
            
            if not shapes:
                print("[ERROR] 没有找到有效的形状对象")
                return False, None
                
            # BRP格式转换逻辑
            print(f"[INFO] 正在转换为BRP格式 (精度: {precision})...")
            
            # 文件输出
            with open(output_path, 'w') as f:
                # 写入BRP文件头
                f.write("BRP 1.0\n")  # 版本信息
                
                if include_metadata:
                    # 写入元数据
                    f.write(f"# 生成时间: {time.ctime()}\n")
                    f.write(f"# 源文件: {os.path.basename(input_path)}\n")
                    f.write(f"# 对象数量: {len(shapes)}\n")
                
                # 写入实际数据
                for i, shape in enumerate(shapes):
                    f.write(f"OBJECT {i+1}\n")
                    f.write(f"FACES {len(shape.Faces)}\n")
                    
                    # 处理每个面
                    for j, face in enumerate(shape.Faces):
                        f.write(f"FACE {j+1}\n")
                        
                        # 提取面的边界表示
                        try:
                            # 写入面的顶点数据
                            vertices = []
                            for edge in face.Edges:
                                for vertex in edge.Vertexes:
                                    vertex_pos = vertex.Point
                                    vertices.append((vertex_pos.x, vertex_pos.y, vertex_pos.z))
                            
                            # 移除重复顶点
                            unique_vertices = []
                            for v in vertices:
                                if v not in unique_vertices:
                                    unique_vertices.append(v)
                            
                            # 写入顶点信息
                            f.write(f"VERTICES {len(unique_vertices)}\n")
                            for k, v in enumerate(unique_vertices):
                                f.write(f"V {k+1} {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                            
                            # 写入边信息
                            f.write(f"EDGES {len(face.Edges)}\n")
                            for k, edge in enumerate(face.Edges):
                                # 简化处理，只记录起点和终点
                                if len(edge.Vertexes) >= 2:
                                    start = edge.Vertexes[0].Point
                                    end = edge.Vertexes[-1].Point
                                    
                                    # 找到对应的顶点索引
                                    start_idx = -1
                                    end_idx = -1
                                    for idx, v in enumerate(unique_vertices):
                                        if abs(v[0]-start.x) < 1e-6 and abs(v[1]-start.y) < 1e-6 and abs(v[2]-start.z) < 1e-6:
                                            start_idx = idx + 1
                                        if abs(v[0]-end.x) < 1e-6 and abs(v[1]-end.y) < 1e-6 and abs(v[2]-end.z) < 1e-6:
                                            end_idx = idx + 1
                                    
                                    if start_idx > 0 and end_idx > 0:
                                        f.write(f"E {k+1} {start_idx} {end_idx}\n")
                        except Exception as e:
                            f.write(f"# 处理面时出错: {str(e)}\n")
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] BRP文件生成成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 输出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STEP到BRP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为BRP成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STEP到BRP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
                
            return False, None
    
    def input_format(self):
        return "step"
    
    def output_format(self):
        return "brp"


class BRPToSTEPConverter(BaseConverter):
    """将BRP文件转换为STEP文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将BRP文件转换为STEP文件
        
        参数:
            input_path: BRP文件路径
            output_path: 输出STEP文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.step")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始BRP到STEP转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 记录输入文件信息
            file_size = os.path.getsize(input_path) / 1024.0
            print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            
            # 创建FreeCAD文档
            doc = FreeCAD.newDocument("TempDoc")
            
            # 解析BRP文件并创建形状
            print("[INFO] 正在解析BRP文件...")
            
            # 读取BRP文件内容
            with open(input_path, 'r') as f:
                lines = f.readlines()
            
            # 验证BRP文件头
            if not lines or not lines[0].startswith("BRP"):
                print("[ERROR] 无效的BRP文件格式")
                return False, None
                
            # 解析BRP数据并创建形状
            print("[INFO] 正在创建形状对象...")
            
            # 解析BRP文件内容
            vertices = []
            faces = []
            current_object = None
            current_face = None
            face_vertices = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) == 0:
                    continue
                
                if parts[0] == "OBJECT":
                    current_object = int(parts[1])
                    print(f"[INFO] 解析对象 {current_object}")
                    
                elif parts[0] == "FACE":
                    if current_face is not None and face_vertices:
                        faces.append(face_vertices)
                    
                    current_face = int(parts[1])
                    face_vertices = []
                    
                elif parts[0] == "V" and len(parts) >= 5:
                    # 顶点格式: V index x y z
                    vertex_idx = int(parts[1])
                    x = float(parts[2])
                    y = float(parts[3])
                    z = float(parts[4])
                    
                    # 确保顶点索引是连续的
                    while len(vertices) < vertex_idx:
                        vertices.append(None)
                    vertices[vertex_idx-1] = (x, y, z)
                    
                elif parts[0] == "E" and len(parts) >= 4:
                    # 边格式: E index v1 v2
                    v1_idx = int(parts[2]) - 1
                    v2_idx = int(parts[3]) - 1
                    
                    if 0 <= v1_idx < len(vertices) and 0 <= v2_idx < len(vertices):
                        if vertices[v1_idx] not in face_vertices:
                            face_vertices.append(vertices[v1_idx])
                        if vertices[v2_idx] not in face_vertices:
                            face_vertices.append(vertices[v2_idx])
            
            # 添加最后一个面
            if current_face is not None and face_vertices:
                faces.append(face_vertices)
            
            # 创建形状
            shape_obj = doc.addObject("Part::Feature", "BRPShape")
            compound = []
            
            try:
                # 从点创建面
                for i, face_verts in enumerate(faces):
                    if len(face_verts) >= 3:
                        # 创建线段
                        edges = []
                        for j in range(len(face_verts)):
                            p1 = face_verts[j]
                            p2 = face_verts[(j+1) % len(face_verts)]
                            p1_vec = FreeCAD.Vector(p1[0], p1[1], p1[2])
                            p2_vec = FreeCAD.Vector(p2[0], p2[1], p2[2])
                            edge = Part.makeLine(p1_vec, p2_vec)
                            edges.append(edge)
                        
                        # 创建线圈
                        try:
                            wire = Part.Wire(edges)
                            if wire.isClosed():
                                face = Part.Face(wire)
                                compound.append(face)
                        except:
                            print(f"[WARNING] 无法为面 {i+1} 创建有效的面")
                
                # 创建复合形状
                if compound:
                    shape = Part.makeCompound(compound)
                    shape_obj.Shape = shape
                else:
                    print("[WARNING] 没有创建任何有效面")
            except Exception as e:
                print(f"[WARNING] 创建形状时出错: {str(e)}")
            
            # 导出为STEP文件
            print("[INFO] 正在导出为STEP文件...")
            
            # 导出STEP
            Part.export([shape_obj], output_path)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STEP文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] BRP到STEP转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STEP成功: {output_path}")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] BRP到STEP转换失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
                
            return False, None
    
    def input_format(self):
        return "brp"
    
    def output_format(self):
        return "step"


import shutil
from api.utils.file_utils import add_random_prefix
# 测试代码
if __name__ == "__main__":
    # 测试STEP到BRP转换 - 使用自动生成的输出路径
    input_file_path = "C:\\Users\\13016\\Downloads\\good.step"
    if os.path.exists(input_file_path):
        # 创建拷贝以避免影响原文件
        copy_path = "C:\\Users\\13016\\Downloads\\good222.step"
        shutil.copyfile(input_file_path, copy_path)
        test_path = add_random_prefix(copy_path)
        
        print(f"[INFO] 测试STEP到BRP转换，使用自动输出路径")
        converter = STEPToBRPConverter()
        success, output_path = converter.convert(test_path)
        print(f"[RESULT] STEP到BRP转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试BRP到STEP转换 - 使用自动生成的输出路径
            brp_input_path = output_path  # 使用前一步的输出作为输入
            print(f"[INFO] 测试BRP到STEP转换，使用自动输出路径")
            converter = BRPToSTEPConverter()
            success, output_path = converter.convert(brp_input_path)
            print(f"[RESULT] BRP到STEP转换结果: {'成功' if success else '失败'}")
    else:
        print(f"[ERROR] 测试文件不存在: {input_file_path}")
    
    print("=" * 50)
    print("[INFO] 插件转换测试完成")
    print("=" * 50)
