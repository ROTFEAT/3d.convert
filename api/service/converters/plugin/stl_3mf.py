import sys
from api.service.converters.base import BaseConverter
import trimesh
import os
import time

class STLTo3MFConverter(BaseConverter):
    """将STL文件转换为3MF文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为3MF文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出3MF文件路径，如果为None则自动生成
            kwargs: 其他可选参数
        """
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.3mf")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到3MF转换: {input_path} -> {output_path}")
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
            
            # 导出为3MF文件
            print("[INFO] 正在导出为3MF文件...")
            mesh.export(output_path, file_type='3mf')
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] 3MF文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STL到3MF转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为3MF成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到3MF转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
        
    def input_format(self):
        return "stl"

    def output_format(self):
        return "3mf"


class ThreeMFToSTLConverter(BaseConverter):
    """将3MF文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将3MF文件转换为STL文件
        
        参数:
            input_path: 3MF文件路径
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
        print(f"[INFO] 开始3MF到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载3MF文件
            print("[INFO] 正在加载3MF文件...")
            mesh = trimesh.load(input_path)
            
            # 处理复杂的3MF文件，可能包含多个网格
            if isinstance(mesh, trimesh.Scene):
                print(f"[INFO] 检测到3MF文件包含场景，提取所有网格...")
                # 提取所有网格并合并
                meshes = []
                for geometry_name, geometry in mesh.geometry.items():
                    print(f"[INFO] 提取网格: {geometry_name}")
                    if isinstance(geometry, trimesh.Trimesh):
                        meshes.append(geometry)
                
                if len(meshes) == 1:
                    mesh = meshes[0]
                elif len(meshes) > 1:
                    print(f"[INFO] 合并 {len(meshes)} 个网格...")
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    print("[WARNING] 未在3MF文件中找到有效网格")
                    return False, None
            
            # 记录网格信息
            print(f"[INFO] 成功加载3MF网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 导出为STL文件 - 处理ASCII格式问题
            print(f"[INFO] 正在导出为STL文件 (格式: {'ASCII' if ascii_format else '二进制'})...")
            
            # 使用更通用的方法导出STL
            if ascii_format:
                # 如果要求ASCII格式，先尝试导出为临时文件然后读写
                try:
                    # 尝试多种可能的参数组合
                    try:
                        # 方法1: 尝试使用 file_type='stl_ascii'
                        mesh.export(output_path, file_type='stl_ascii')
                    except (ValueError, TypeError):
                        try:
                            # 方法2: 尝试使用 binary=False
                            mesh.export(output_path, file_type='stl', binary=False)
                        except (ValueError, TypeError):
                            # 方法3: 纯文本方式导出
                            import numpy as np
                            with open(output_path, 'w') as f:
                                f.write("solid exported\n")
                                for i in range(len(mesh.faces)):
                                    face = mesh.faces[i]
                                    normal = mesh.face_normals[i]
                                    f.write(f"facet normal {normal[0]} {normal[1]} {normal[2]}\n")
                                    f.write("  outer loop\n")
                                    for j in range(3):
                                        vertex = mesh.vertices[face[j]]
                                        f.write(f"    vertex {vertex[0]} {vertex[1]} {vertex[2]}\n")
                                    f.write("  endloop\n")
                                    f.write("endfacet\n")
                                f.write("endsolid exported\n")
                except Exception as e:
                    print(f"[WARNING] ASCII导出失败，回退到二进制格式: {str(e)}")
                    # 回退到二进制格式
                    mesh.export(output_path, file_type='stl')
            else:
                # 二进制格式STL (默认)
                mesh.export(output_path, file_type='stl')
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] 3MF到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] 3MF到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "3mf"
    
    def output_format(self):
        return "stl"

from api.utils.file_utils import add_random_prefix

# 测试代码
if __name__ == "__main__":

    print("=" * 50)
    print("[INFO] 开始STL与3MF转换测试")
    print("=" * 50)
    
    # 测试STL到3MF转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    input_file_path = add_random_prefix(input_file_path)
    print("修改文件的名字为", input_file_path)
    print(f"[INFO] 测试STL到3MF转换，使用自动输出路径")
    
    converter = STLTo3MFConverter()
    success, output_path = converter.convert(input_file_path)
    print(f"[RESULT] STL到3MF转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试3MF到STL转换
        input_file_path = output_path
        print(f"[INFO] 测试3MF到STL转换，使用自动输出路径")
        
        converter = ThreeMFToSTLConverter()
        success, output_path = converter.convert(input_file_path)
        print(f"[RESULT] 3MF到STL转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
