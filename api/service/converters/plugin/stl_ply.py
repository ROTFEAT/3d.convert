import sys
from api.service.converters.base import BaseConverter
import trimesh
import os
import time

class STLToPLYConverter(BaseConverter):
    """将STL文件转换为PLY文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为PLY文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出PLY文件路径，如果为None则自动生成
            kwargs: 其他可选参数
                   - ascii: 布尔值，是否使用ASCII格式PLY (默认为False，使用二进制格式)
                   - color: 可选的默认颜色，格式为[r, g, b]，其中r/g/b为0-255的整数值
        """
        # 提取参数
        ascii_format = kwargs.get('ascii', False)
        default_color = kwargs.get('color', None)
        
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.ply")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到PLY转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
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
            
            # 如果提供了颜色参数，为模型添加颜色
            if default_color is not None:
                try:
                    # 确认颜色格式是否正确 (应为 [r, g, b] 数组，每个值在0-255之间)
                    if len(default_color) >= 3 and all(0 <= c <= 255 for c in default_color[:3]):
                        # 转换为标准化的颜色值 (0.0-1.0)
                        color_norm = [c/255.0 for c in default_color[:3]]
                        # 为所有面设置相同的颜色
                        colors = [color_norm] * len(mesh.faces)
                        # 设置面颜色
                        mesh.visual.face_colors = colors
                        print(f"[INFO] 已应用默认颜色: RGB{default_color[:3]}")
                    else:
                        print(f"[WARNING] 颜色格式不正确，已忽略: {default_color}")
                except Exception as e:
                    print(f"[WARNING] 应用颜色失败: {str(e)}，将导出无颜色模型")
            
            # 导出为PLY文件
            print(f"[INFO] 正在导出为PLY文件 (格式: {'ASCII' if ascii_format else '二进制'})...")
            # 设置导出参数
            export_options = {
                'file_type': 'ply',
                'encoding': 'ascii' if ascii_format else 'binary'
            }
            mesh.export(output_path, **export_options)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] PLY文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STL到PLY转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为PLY成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到PLY转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
        
    def input_format(self):
        return "stl"

    def output_format(self):
        return "ply"


class PLYToSTLConverter(BaseConverter):
    """将PLY文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将PLY文件转换为STL文件
        
        参数:
            input_path: PLY文件路径
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
        print(f"[INFO] 开始PLY到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载PLY文件
            print("[INFO] 正在加载PLY文件...")
            mesh = trimesh.load(input_path)
            
            # 记录网格信息
            print(f"[INFO] 成功加载PLY网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 检查是否包含颜色信息
            has_color = False
            try:
                if hasattr(mesh.visual, 'face_colors') and mesh.visual.face_colors is not None:
                    has_color = True
                    print("[INFO] 检测到PLY文件包含颜色信息，转换为STL将丢失这些信息")
            except:
                pass
            
            # 导出为STL文件
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
                if has_color:
                    print("[INFO] 注意: 颜色信息未包含在STL文件中")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] PLY到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] PLY到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "ply"
    
    def output_format(self):
        return "stl"


from api.utils.file_utils import add_random_prefix
import shutil

# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与PLY转换测试")
    print("=" * 50)
    
    # 测试STL到PLY转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    
    # 测试二进制PLY格式
    print(f"[INFO] 测试STL到PLY转换(二进制格式)")
    converter = STLToPLYConverter()
    # 添加红色
    success, ply_binary_path = converter.convert(input_file_path, color=[255, 0, 0])
    print(f"[RESULT] STL到PLY(二进制)转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试PLY到STL转换
        print(f"[INFO] 测试PLY到STL转换，使用自动输出路径")
        converter = PLYToSTLConverter()
        success, stl_path = converter.convert(ply_binary_path)
        print(f"[RESULT] PLY到STL转换结果: {'成功' if success else '失败'}")
        
        print("-" * 40)
        # 测试ASCII PLY格式
        print(f"[INFO] 测试STL到PLY转换(ASCII格式)")
        converter = STLToPLYConverter()
        # 添加绿色
        success, ply_ascii_path = converter.convert(input_file_path, ascii=True, color=[0, 255, 0])
        print(f"[RESULT] STL到PLY(ASCII)转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试PLY到STL ASCII转换
            print(f"[INFO] 测试PLY到STL转换(ASCII格式)")
            converter = PLYToSTLConverter()
            success, stl_ascii_path = converter.convert(ply_ascii_path, ascii=True)
            print(f"[RESULT] PLY到STL(ASCII)转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
