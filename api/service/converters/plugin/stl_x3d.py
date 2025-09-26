import sys
from api.service.converters.base import BaseConverter
import trimesh
import os
import time
import numpy as np
from xml.etree import ElementTree as ET
from xml.dom import minidom

class STLToX3DConverter(BaseConverter):
    """将STL文件转换为X3D文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为X3D文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出X3D文件路径，如果为None则自动生成
            kwargs: 其他可选参数
                   - color: 可选的默认颜色，格式为[r, g, b]，其中r/g/b为0-255的整数值
        """
        # 提取参数
        default_color = kwargs.get('color', [220, 220, 220])  # 默认浅灰色
        
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.x3d")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到X3D转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载STL文件
            print("[INFO] 正在加载STL文件...")
            mesh = trimesh.load(input_path)
            
            # 记录网格信息
            print(f"[INFO] 成功加载STL网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 确保默认颜色格式正确
            if default_color is None:
                default_color = [220, 220, 220]  # 默认浅灰色
            
            # 确认颜色格式是否正确 (应为 [r, g, b] 数组，每个值在0-255之间)
            if len(default_color) >= 3 and all(0 <= c <= 255 for c in default_color[:3]):
                # 转换为标准化的颜色值 (0.0-1.0)
                color_norm = [c/255.0 for c in default_color[:3]]
                color_str = f"{color_norm[0]:.6f} {color_norm[1]:.6f} {color_norm[2]:.6f}"
                print(f"[INFO] 已应用默认颜色: RGB{default_color[:3]}")
            else:
                print(f"[WARNING] 颜色格式不正确，使用默认灰色: {default_color}")
                color_str = "0.8 0.8 0.8"  # 默认灰色
            
            # 由于trimesh不直接支持X3D导出，我们手动创建X3D文件
            print("[INFO] 正在手动创建X3D文件...")
            
            # 创建X3D文档基本结构
            x3d = ET.Element('X3D', {
                'profile': 'Immersive',
                'version': '3.3',
                'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsd:noNamespaceSchemaLocation': 'http://www.web3d.org/specifications/x3d-3.3.xsd'
            })
            
            head = ET.SubElement(x3d, 'head')
            meta = ET.SubElement(head, 'meta', {'name': 'generator', 'content': 'STLToX3DConverter'})
            meta = ET.SubElement(head, 'meta', {'name': 'creator', 'content': 'WantNet 3D Conversion Service'})
            
            scene = ET.SubElement(x3d, 'Scene')
            
            # 创建形状
            shape = ET.SubElement(scene, 'Shape')
            
            # 设置外观
            appearance = ET.SubElement(shape, 'Appearance')
            material = ET.SubElement(appearance, 'Material', {
                'diffuseColor': color_str,
                'shininess': '0.2',
                'specularColor': '0.1 0.1 0.1'
            })
            
            # 创建IndexedFaceSet
            ifs = ET.SubElement(shape, 'IndexedFaceSet', {
                'solid': 'true',
                'coordIndex': ' '.join(
                    [' '.join([str(int(idx)) for idx in face] + ['-1']) for face in mesh.faces]
                )
            })
            
            # 添加顶点坐标
            coordinate = ET.SubElement(ifs, 'Coordinate', {
                'point': ' '.join([' '.join([f"{v:.6f}" for v in vertex]) for vertex in mesh.vertices])
            })
            
            # 如果有法线，添加法线
            if hasattr(mesh, 'face_normals') and mesh.face_normals is not None:
                normal = ET.SubElement(ifs, 'Normal', {
                    'vector': ' '.join([' '.join([f"{n:.6f}" for n in norm]) for norm in mesh.face_normals])
                })
            
            # 将XML转换为字符串并格式化
            rough_string = ET.tostring(x3d, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            x3d_str = reparsed.toprettyxml(indent="  ")
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(x3d_str)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] X3D文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STL到X3D转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为X3D成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到X3D转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
        
    def input_format(self):
        return "stl"

    def output_format(self):
        return "x3d"


class X3DToSTLConverter(BaseConverter):
    """将X3D文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将X3D文件转换为STL文件
        
        参数:
            input_path: X3D文件路径
            output_path: 输出STL文件路径，如果为None则自动生成
            kwargs: 其他可选参数，如:
                   - ascii: 布尔值，是否使用ASCII格式STL (默认为False，使用二进制格式)
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.stl")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
            
        # 提取参数
        ascii_format = kwargs.get('ascii', False)
        print(f"[INFO] 开始X3D到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # ===== 基本XML解析 =====
            # 首先尝试最简单直接的方法 - 直接解析我们自己生成的X3D格式
            try:
                print("[INFO] 尝试直接解析X3D XML文件...")
                tree = ET.parse(input_path)
                root = tree.getroot()
                
                vertices = []
                faces = []
                
                # 寻找坐标节点
                coord_nodes = root.findall('.//Coordinate')
                if coord_nodes:
                    for coord_node in coord_nodes:
                        if 'point' in coord_node.attrib:
                            point_str = coord_node.attrib['point']
                            # 解析点坐标
                            coords = [float(x) for x in point_str.split()]
                            # 每3个值为一个顶点
                            for i in range(0, len(coords), 3):
                                if i+2 < len(coords):
                                    vertices.append([coords[i], coords[i+1], coords[i+2]])
                
                # 寻找面索引
                ifs_nodes = root.findall('.//IndexedFaceSet')
                if ifs_nodes:
                    for ifs_node in ifs_nodes:
                        if 'coordIndex' in ifs_node.attrib:
                            index_str = ifs_node.attrib['coordIndex']
                            # 解析索引
                            indices = [int(x) for x in index_str.split() if x != '-1']
                            
                            # 每三个索引形成一个面
                            # 注意：索引数可能不是3的倍数，这里我们需要小心处理
                            current_face = []
                            for idx in index_str.split():
                                if idx == '-1':
                                    if len(current_face) >= 3:
                                        faces.append(current_face)
                                    current_face = []
                                else:
                                    current_face.append(int(idx))
                            
                            # 处理最后一个面（如果没有-1结尾）
                            if current_face and len(current_face) >= 3:
                                faces.append(current_face)
                
                # 检查是否成功解析出顶点和面
                if vertices and faces:
                    print(f"[INFO] 成功解析X3D数据: {len(vertices)} 顶点, {len(faces)} 面")
                    
                    # 将解析出的数据转换为trimesh网格
                    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                    
                    # 导出为STL
                    if ascii_format:
                        # ASCII格式
                        try:
                            mesh.export(output_path, file_type='stl_ascii')
                        except Exception as ascii_err:
                            print(f"[WARNING] ASCII导出失败，使用二进制格式: {str(ascii_err)}")
                            mesh.export(output_path, file_type='stl')
                    else:
                        # 二进制格式
                        mesh.export(output_path, file_type='stl')
                    
                    # 验证输出文件
                    if os.path.exists(output_path):
                        output_size = os.path.getsize(output_path) / 1024.0
                        print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                        
                        end_time = time.time()
                        print(f"[INFO] X3D到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
                        print(f"[SUCCESS] 转换为STL成功: {output_path}")
                        return True, output_path
                
                print("[INFO] 使用基本XML解析未能提取足够的网格数据，尝试其他方法...")
            
            except Exception as xml_err:
                print(f"[WARNING] 基本XML解析失败: {str(xml_err)}")
            
            # ===== 使用临时OBJ文件作为中介 =====
            # 这是一个备选方案，如果直接解析失败
            try:
                print("[INFO] 尝试创建临时OBJ文件...")
                
                # 创建临时文件路径
                temp_dir = os.path.dirname(input_path)
                temp_basename = os.path.splitext(os.path.basename(input_path))[0]
                temp_obj_path = os.path.join(temp_dir, f"temp_{temp_basename}.obj")
                
                # 检查我们是否已经成功解析了顶点和面
                if 'vertices' in locals() and vertices and 'faces' in locals() and faces:
                    # 如果已经有解析出的数据，直接使用
                    print("[INFO] 使用已解析的数据创建OBJ...")
                    
                    # 写入OBJ文件
                    with open(temp_obj_path, 'w') as f:
                        # 写入顶点
                        for vertex in vertices:
                            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
                        
                        # 写入面（OBJ索引从1开始）
                        for face in faces:
                            # 确保每个面至少有3个顶点
                            if len(face) >= 3:
                                f.write(f"f {' '.join([str(idx+1) for idx in face])}\n")
                    
                    print(f"[INFO] 临时OBJ文件创建成功: {temp_obj_path}")
                    
                    # 使用trimesh加载OBJ并导出为STL
                    mesh = trimesh.load(temp_obj_path)
                    
                    # 如果加载成功
                    if mesh is not None:
                        print(f"[INFO] 成功从临时OBJ加载网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
                        
                        # 导出为STL
                        if ascii_format:
                            try:
                                mesh.export(output_path, file_type='stl_ascii')
                            except Exception:
                                mesh.export(output_path, file_type='stl')
                        else:
                            mesh.export(output_path, file_type='stl')
                        
                        # 删除临时文件
                        if os.path.exists(temp_obj_path):
                            os.remove(temp_obj_path)
                            print("[INFO] 临时OBJ文件已删除")
                        
                        # 验证输出文件
                        if os.path.exists(output_path):
                            output_size = os.path.getsize(output_path) / 1024.0
                            print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                            
                            end_time = time.time()
                            print(f"[INFO] X3D到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
                            print(f"[SUCCESS] 转换为STL成功: {output_path}")
                            return True, output_path
                
                print("[INFO] OBJ中介转换未成功，尝试最后方法...")
            
            except Exception as obj_err:
                print(f"[WARNING] 临时OBJ文件处理失败: {str(obj_err)}")
            
            # ===== 安全使用pymeshlab（如果可用） =====
            # 最后尝试pymeshlab，但在单独的进程中运行以避免崩溃
            import subprocess
            import sys
            
            # 创建一个临时脚本来使用pymeshlab
            temp_script_path = os.path.join(os.path.dirname(input_path), "temp_convert_script.py")
            
            try:
                print("[INFO] 尝试使用pymeshlab（在安全模式下）...")
                
                # 创建一个简单的转换脚本
                with open(temp_script_path, 'w') as f:
                    f.write('import sys\n')
                    f.write('try:\n')
                    f.write('    import pymeshlab\n')
                    f.write(f'    ms = pymeshlab.MeshSet()\n')
                    f.write(f'    ms.load_new_mesh("{input_path}")\n')
                    f.write(f'    ms.save_current_mesh("{output_path}", save_face_color=False, binary={not ascii_format})\n')
                    f.write('    print("SUCCESS")\n')
                    f.write('except Exception as e:\n')
                    f.write('    print(f"ERROR: {e}")\n')
                
                # 在单独的进程中运行脚本
                result = subprocess.run([sys.executable, temp_script_path], 
                                       capture_output=True, text=True)
                
                # 检查结果
                if "SUCCESS" in result.stdout:
                    print("[INFO] pymeshlab处理成功")
                    
                    # 验证输出文件
                    if os.path.exists(output_path):
                        output_size = os.path.getsize(output_path) / 1024.0
                        print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                        
                        end_time = time.time()
                        print(f"[INFO] X3D到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
                        print(f"[SUCCESS] 转换为STL成功: {output_path}")
                        
                        # 删除临时脚本
                        if os.path.exists(temp_script_path):
                            os.remove(temp_script_path)
                        
                        return True, output_path
                else:
                    print(f"[WARNING] pymeshlab处理失败: {result.stdout}")
            
            except Exception as script_err:
                print(f"[WARNING] 安全模式下的pymeshlab处理失败: {str(script_err)}")
            
            # 删除临时脚本
            if os.path.exists(temp_script_path):
                try:
                    os.remove(temp_script_path)
                except:
                    pass
            
            # 如果所有方法都失败了
            print("[ERROR] 所有X3D到STL转换方法都失败")
            return False, None
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] X3D到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "x3d"
    
    def output_format(self):
        return "stl"


from api.utils.file_utils import add_random_prefix
import shutil

# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与X3D转换测试")
    print("=" * 50)
    
    # 测试STL到X3D转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    
    # 测试X3D格式 - 添加蓝色
    print(f"[INFO] 测试STL到X3D转换")
    converter = STLToX3DConverter()
    success, x3d_path = converter.convert(input_file_path, color=[0, 0, 255])
    print(f"[RESULT] STL到X3D转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试X3D到STL转换
        print(f"[INFO] 测试X3D到STL转换，使用二进制格式")
        converter = X3DToSTLConverter()
        success, stl_path = converter.convert(x3d_path)
        print(f"[RESULT] X3D到STL(二进制)转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试X3D到STL ASCII转换
            print(f"[INFO] 测试X3D到STL转换，使用ASCII格式")
            converter = X3DToSTLConverter()
            success, stl_ascii_path = converter.convert(x3d_path, ascii=True)
            print(f"[RESULT] X3D到STL(ASCII)转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
