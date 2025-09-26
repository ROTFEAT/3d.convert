import sys
from api.service.converters.base import BaseConverter
import trimesh
import os
import time

class STLToGLTFConverter(BaseConverter):
    """将STL文件转换为GLTF文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为GLTF文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出GLTF文件路径，如果为None则自动生成
            kwargs: 其他可选参数
                   - binary: 布尔值，是否导出为二进制GLB格式 (默认为False，导出为JSON格式GLTF)
        """
        # 提取参数
        binary_format = kwargs.get('binary', False)
        file_extension = '.glb' if binary_format else '.gltf'
        export_format = 'glb' if binary_format else 'gltf'
        
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}{file_extension}")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到GLTF转换: {input_path} -> {output_path} (格式: {'二进制GLB' if binary_format else 'JSON GLTF'})")
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
            
            # 由于glTF通常需要场景对象，我们创建一个包含此网格的场景
            print("[INFO] 创建场景并添加网格...")
            scene = trimesh.Scene()
            scene.add_geometry(mesh)
            
            # 导出为GLTF/GLB文件
            print(f"[INFO] 正在导出为{export_format.upper()}文件...")
            scene.export(output_path, file_type=export_format)
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] {export_format.upper()}文件导出成功: {output_size:.2f} KB")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] STL到{export_format.upper()}转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为{export_format.upper()}成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到GLTF转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
        
    def input_format(self):
        return "stl"

    def output_format(self):
        return "gltf"


class GLTFToSTLConverter(BaseConverter):
    """将GLTF/GLB文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将GLTF/GLB文件转换为STL文件
        
        参数:
            input_path: GLTF或GLB文件路径
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
        input_format = os.path.splitext(input_path)[1].lower()
        if input_format in ['.gltf', '.glb']:
            input_format = input_format[1:]  # 去掉点号
        else:
            input_format = 'gltf'  # 默认假设为gltf格式
            
        print(f"[INFO] 开始{input_format.upper()}到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 加载GLTF/GLB文件
            print(f"[INFO] 正在加载{input_format.upper()}文件...")
            # 导入文件通常返回一个场景
            scene = trimesh.load(input_path)
            
            # 处理场景中的所有网格
            if isinstance(scene, trimesh.Scene):
                print(f"[INFO] 检测到{input_format.upper()}文件包含场景，提取所有网格...")
                # 提取所有网格并合并
                meshes = []
                for geometry_name, geometry in scene.geometry.items():
                    print(f"[INFO] 提取网格: {geometry_name}")
                    if isinstance(geometry, trimesh.Trimesh):
                        # 将网格转换到场景坐标系
                        transform = scene.graph.get(geometry_name)[0]
                        geometry = geometry.copy()
                        geometry.apply_transform(transform)
                        meshes.append(geometry)
                
                if len(meshes) == 1:
                    mesh = meshes[0]
                elif len(meshes) > 1:
                    print(f"[INFO] 合并 {len(meshes)} 个网格...")
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    print(f"[WARNING] 未在{input_format.upper()}文件中找到有效网格")
                    return False, None
            elif isinstance(scene, trimesh.Trimesh):
                # 直接是单个网格
                mesh = scene
            else:
                print(f"[ERROR] 无法处理的{input_format.upper()}文件格式")
                return False, None
            
            # 记录网格信息
            print(f"[INFO] 成功加载{input_format.upper()}网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
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
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] {input_format.upper()}到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] GLTF到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "gltf"
    
    def output_format(self):
        return "stl"


from api.utils.file_utils import add_random_prefix
import shutil
# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与GLTF转换测试")
    print("=" * 50)
    
    # 测试STL到GLTF转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    print(f"[INFO] 测试STL到GLTF转换，使用自动输出路径")
    
    # 先测试导出为JSON格式的GLTF
    converter = STLToGLTFConverter()
    success, output_path = converter.convert(input_file_path, binary=False)
    print(f"[RESULT] STL到GLTF(JSON)转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试GLTF到STL转换
        gltf_path = output_path
        print(f"[INFO] 测试GLTF到STL转换，使用自动输出路径")
        
        converter = GLTFToSTLConverter()
        success, stl_path = converter.convert(gltf_path)
        print(f"[RESULT] GLTF到STL转换结果: {'成功' if success else '失败'}")
        
        print("-" * 40)
        # 再测试导出为二进制格式的GLB
        print(f"[INFO] 测试STL到GLB(二进制)转换，使用自动输出路径")
        converter = STLToGLTFConverter()
        success, glb_path = converter.convert(input_file_path, binary=True)
        print(f"[RESULT] STL到GLB(二进制)转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试GLB到STL转换
            print(f"[INFO] 测试GLB到STL转换，使用自动输出路径")
            converter = GLTFToSTLConverter()
            success, stl_path2 = converter.convert(glb_path)
            print(f"[RESULT] GLB到STL转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
