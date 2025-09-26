import sys
from api.service.converters.base import BaseConverter
import trimesh
import os
import time
import numpy as np
import subprocess

class STLTo3DSConverter(BaseConverter):
    """将STL文件转换为3DS文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为3DS文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出3DS文件路径，如果为None则自动生成
            kwargs: 其他可选参数
                   - color: 可选的默认颜色，格式为[r, g, b]，其中r/g/b为0-255的整数值
        """
        # 提取参数
        default_color = kwargs.get('color', None)
        
        # 如果没有提供输出路径，自动生成一个
        if not output_path:
            # 获取输入文件的目录和文件名（不含扩展名）
            input_dir = os.path.dirname(input_path)
            input_basename = os.path.splitext(os.path.basename(input_path))[0]
            # 生成输出文件路径
            output_path = os.path.join(input_dir, f"{input_basename}.3ds")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到3DS转换: {input_path} -> {output_path}")
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
                        colors = np.ones((len(mesh.faces), 4))
                        colors[:, 0:3] = color_norm
                        # 设置面颜色
                        mesh.visual.face_colors = colors
                        print(f"[INFO] 已应用默认颜色: RGB{default_color[:3]}")
                    else:
                        print(f"[WARNING] 颜色格式不正确，忽略颜色参数: {default_color}")
                except Exception as e:
                    print(f"[WARNING] 设置颜色失败: {str(e)}")
            
            # 尝试使用FreeCAD进行转换
            success = self._try_freecad_conversion(input_path, output_path)
            if success:
                # 验证输出文件
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    output_size = os.path.getsize(output_path) / 1024.0
                    print(f"[INFO] 3DS文件导出成功: {output_size:.2f} KB")
                    
                    end_time = time.time()
                    print(f"[INFO] STL到3DS转换完成! 用时: {end_time - start_time:.2f} 秒")
                    print(f"[SUCCESS] 转换为3DS成功: {output_path}")
                    return True, output_path
                else:
                    print("[WARNING] FreeCAD转换完成但未生成有效文件，尝试其他方法...")
            else:
                print("[INFO] FreeCAD转换不可用，尝试其他方法...")
            
            # 使用中间格式（OBJ）作为转换桥梁，然后尝试使用Blender
            print("[INFO] 通过OBJ中间格式进行转换...")
            temp_obj = os.path.join(os.path.dirname(input_path), f"temp_{os.path.basename(input_path)}.obj")
            
            try:
                # 导出为OBJ中间格式
                mesh.export(temp_obj, file_type='obj')
                print(f"[INFO] 已创建临时OBJ文件: {temp_obj}")
                
                # 尝试使用Blender（如果可用）
                print("[INFO] 尝试使用Blender...")
                
                blender_path = None
                # 尝试常见的Blender安装路径
                for path in [
                    "blender",  # 如果在PATH中
                    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
                    r"/Applications/Blender.app/Contents/MacOS/Blender",
                    r"/usr/bin/blender"
                ]:
                    try:
                        subprocess.run([path, "--version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
                        blender_path = path
                        break
                    except:
                        continue
                
                if blender_path:
                    # 创建Blender脚本
                    blender_script = os.path.join(os.path.dirname(input_path), "temp_blender_3ds.py")
                    with open(blender_script, 'w') as f:
                        f.write('import bpy\n')
                        f.write('bpy.ops.wm.read_factory_settings(use_empty=True)\n')
                        f.write('bpy.ops.import_scene.obj(filepath=r"%s")\n' % temp_obj.replace('\\', '\\\\'))
                        f.write('bpy.ops.export_scene.autodesk_3ds(filepath=r"%s")\n' % output_path.replace('\\', '\\\\'))
                    
                    try:
                        subprocess.run([blender_path, "--background", "--python", blender_script], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            print("[INFO] Blender转换成功")
                        else:
                            print("[WARNING] Blender导出文件无效")
                            
                    except Exception as blender_err:
                        print(f"[WARNING] Blender处理失败: {str(blender_err)}")
                        
                    # 删除临时脚本
                    if os.path.exists(blender_script):
                        os.remove(blender_script)
                else:
                    print("[WARNING] 找不到Blender可执行文件")
                
                # 删除临时OBJ文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
                    print("[INFO] 删除临时OBJ文件")
                
            except Exception as obj_err:
                print(f"[WARNING] OBJ中间格式转换失败: {str(obj_err)}")
                # 确保删除临时文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
            
            # 尝试使用PyMeshLab（如果可用）
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print("[INFO] 尝试使用PyMeshLab...")
                try:
                    import pymeshlab
                    ms = pymeshlab.MeshSet()
                    ms.load_new_mesh(input_path)
                    ms.save_current_mesh(output_path)
                    print("[INFO] PyMeshLab转换成功")
                except ImportError:
                    print("[WARNING] PyMeshLab不可用")
                except Exception as meshlabErr:
                    print(f"[WARNING] PyMeshLab转换失败: {str(meshlabErr)}")
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] 3DS文件导出成功: {output_size:.2f} KB")
                
                end_time = time.time()
                print(f"[INFO] STL到3DS转换完成! 用时: {end_time - start_time:.2f} 秒")
                print(f"[SUCCESS] 转换为3DS成功: {output_path}")
                return True, output_path
            else:
                print("[ERROR] 导出失败: 输出文件未创建或为空")
                return False, None
                
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到3DS转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def _try_freecad_conversion(self, input_path, output_path):
        """
        尝试使用FreeCAD进行STL到3DS的转换
        """
        print("[INFO] 尝试使用FreeCAD进行转换...")
        
        try:
            # 尝试导入FreeCAD模块
            try:
                import FreeCAD
                import Mesh
                print("[INFO] 成功导入FreeCAD模块")
            except ImportError:
                print("[WARNING] 无法导入FreeCAD模块，FreeCAD可能未安装或未添加到Python路径")
                return False
            
            # 设置FreeCAD无GUI模式
            import os
            os.environ["FREECAD_NO_GUI"] = "1"
            
            # 创建一个新文档
            doc = FreeCAD.newDocument("STLto3DS")
            print(f"[INFO] 创建FreeCAD文档: STLto3DS")
            
            # 导入STL文件
            print(f"[INFO] 导入STL文件: {input_path}")
            Mesh.insert(input_path, doc.Name)
            
            # 检查是否成功导入
            if len(doc.Objects) == 0:
                print("[ERROR] 导入STL文件失败，未创建任何对象")
                FreeCAD.closeDocument(doc.Name)
                return False
            
            # 获取导入的网格对象
            mesh_obj = doc.Objects[0]
            print(f"[INFO] 获取到导入的网格对象: {mesh_obj.Name}")
            
            try:
                # 导出为中间OBJ文件
                temp_obj = input_path + ".temp.obj"
                print(f"[INFO] 创建临时OBJ文件: {temp_obj}")
                
                # 使用FreeCAD的Mesh模块导出OBJ
                Mesh.export([mesh_obj], temp_obj)
                
                # 检查临时文件是否成功创建
                if not os.path.exists(temp_obj) or os.path.getsize(temp_obj) == 0:
                    print("[ERROR] 临时OBJ文件创建失败")
                    raise Exception("临时OBJ文件创建失败")
                
                # 使用MeshLab进行OBJ到3DS的转换（如果可用）
                try:
                    # 尝试使用PyMeshLab
                    print("[INFO] 尝试使用PyMeshLab将OBJ转换为3DS...")
                    import pymeshlab
                    ms = pymeshlab.MeshSet()
                    ms.load_new_mesh(temp_obj)
                    ms.save_current_mesh(output_path)
                    print("[INFO] PyMeshLab转换成功")
                    
                    # 验证输出文件
                    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                        raise Exception("导出文件无效")
                        
                except ImportError:
                    # 如果PyMeshLab不可用，尝试使用Blender
                    print("[INFO] PyMeshLab不可用，尝试使用Blender...")
                    blender_path = None
                    
                    # 查找Blender可执行文件
                    for path in [
                        "blender",  # 如果在PATH中
                        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
                        r"/Applications/Blender.app/Contents/MacOS/Blender",
                        r"/usr/bin/blender"
                    ]:
                        try:
                            subprocess.run([path, "--version"], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE)
                            blender_path = path
                            break
                        except:
                            continue
                    
                    if blender_path:
                        # 创建Blender脚本
                        blender_script = os.path.join(os.path.dirname(input_path), "temp_blender_3ds.py")
                        with open(blender_script, 'w') as f:
                            f.write('import bpy\n')
                            f.write('bpy.ops.wm.read_factory_settings(use_empty=True)\n')
                            f.write('bpy.ops.import_scene.obj(filepath=r"%s")\n' % temp_obj.replace('\\', '\\\\'))
                            f.write('bpy.ops.export_scene.autodesk_3ds(filepath=r"%s")\n' % output_path.replace('\\', '\\\\'))
                        
                        # 执行Blender脚本
                        subprocess.run([blender_path, "--background", "--python", blender_script], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                        
                        # 删除临时脚本
                        if os.path.exists(blender_script):
                            os.remove(blender_script)
                            
                        # 验证输出
                        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                            raise Exception("Blender导出文件无效")
                    else:
                        raise Exception("找不到Blender可执行文件")
                        
                except Exception as conv_err:
                    print(f"[WARNING] 转换失败: {str(conv_err)}")
                    raise
                    
            except Exception as e:
                print(f"[ERROR] FreeCAD通过中间格式转换失败: {e}")
                # 关闭文档
                FreeCAD.closeDocument(doc.Name)
                # 删除临时文件
                if 'temp_obj' in locals() and os.path.exists(temp_obj):
                    os.remove(temp_obj)
                return False
                
            # 删除临时OBJ文件
            if 'temp_obj' in locals() and os.path.exists(temp_obj):
                os.remove(temp_obj)
                print("[INFO] 删除临时OBJ文件")
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            print("[INFO] 关闭FreeCAD文档")
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[INFO] 3DS文件导出成功")
                return True
            else:
                print("[ERROR] 导出文件不存在或为空")
                return False
                
        except Exception as e:
            print(f"[ERROR] FreeCAD转换过程出错: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            
            # 确保文档被关闭
            try:
                if 'doc' in locals() and doc:
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
            
            # 删除临时文件
            if 'temp_obj' in locals() and os.path.exists(temp_obj):
                try:
                    os.remove(temp_obj)
                except:
                    pass
                    
            return False

    def input_format(self):
        return "stl"

    def output_format(self):
        return "3ds"


class ThreeDSToSTLConverter(BaseConverter):
    """将3DS文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将3DS文件转换为STL文件
        
        参数:
            input_path: 3DS文件路径
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
        print(f"[INFO] 开始3DS到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 尝试使用FreeCAD进行转换
            success = self._try_freecad_conversion(input_path, output_path, ascii_format)
            
            if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                end_time = time.time()
                print(f"[INFO] 3DS到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
                print(f"[SUCCESS] 转换为STL成功: {output_path}")
                return True, output_path
                
            # 如果FreeCAD转换失败，尝试其他方法
            print("[INFO] 尝试使用其他方法进行转换...")
            
            # 尝试使用PyMeshLab
            try:
                print("[INFO] 尝试使用PyMeshLab...")
                import pymeshlab
                ms = pymeshlab.MeshSet()
                ms.load_new_mesh(input_path)
                
                # 直接导出STL
                stl_type = 'ascii' if ascii_format else 'binary'
                ms.save_current_mesh(output_path, save_face_color=True, binary=not ascii_format)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print("[INFO] PyMeshLab转换成功")
                    success = True
                else:
                    raise Exception("导出文件无效")
                    
            except ImportError:
                print("[WARNING] PyMeshLab不可用")
                success = False
            except Exception as e:
                print(f"[WARNING] PyMeshLab转换失败: {str(e)}")
                success = False
            
            # 尝试使用Blender
            if not success or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print("[INFO] 尝试使用Blender...")
                
                blender_path = None
                # 尝试常见的Blender安装路径
                for path in [
                    "blender",  # 如果在PATH中
                    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
                    r"/Applications/Blender.app/Contents/MacOS/Blender",
                    r"/usr/bin/blender"
                ]:
                    try:
                        subprocess.run([path, "--version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
                        blender_path = path
                        break
                    except:
                        continue
                
                if blender_path:
                    # 创建Blender脚本
                    blender_script = os.path.join(os.path.dirname(input_path), "temp_blender_stl.py")
                    with open(blender_script, 'w') as f:
                        f.write('import bpy\n')
                        f.write('bpy.ops.wm.read_factory_settings(use_empty=True)\n')
                        f.write('bpy.ops.import_scene.autodesk_3ds(filepath=r"%s")\n' % input_path.replace('\\', '\\\\'))
                        f.write('bpy.ops.export_mesh.stl(filepath=r"%s", ascii=%s)\n' % 
                               (output_path.replace('\\', '\\\\'), str(ascii_format).lower()))
                    
                    try:
                        subprocess.run([blender_path, "--background", "--python", blender_script], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            print("[INFO] Blender转换成功")
                            success = True
                        else:
                            print("[WARNING] Blender导出文件无效")
                            
                    except Exception as blender_err:
                        print(f"[WARNING] Blender处理失败: {str(blender_err)}")
                        
                    # 删除临时脚本
                    if os.path.exists(blender_script):
                        os.remove(blender_script)
            
            # 验证最终结果
            if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                
                end_time = time.time()
                print(f"[INFO] 3DS到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
                print(f"[SUCCESS] 转换为STL成功: {output_path}")
                return True, output_path
            else:
                print("[ERROR] 所有转换方法均失败")
                return False, None
                
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] 3DS到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def _try_freecad_conversion(self, input_path, output_path, ascii_format=False):
        """
        尝试使用FreeCAD进行3DS到STL的转换
        """
        print("[INFO] 尝试使用FreeCAD进行转换...")
        
        try:
            # 尝试导入FreeCAD模块
            try:
                import FreeCAD
                import Mesh
                print("[INFO] 成功导入FreeCAD模块")
            except ImportError:
                print("[WARNING] 无法导入FreeCAD模块，FreeCAD可能未安装或未添加到Python路径")
                return False
            
            # 设置FreeCAD无GUI模式
            import os
            os.environ["FREECAD_NO_GUI"] = "1"
            
            # 创建临时OBJ文件作为中间格式
            temp_obj = input_path + ".temp.obj"
            
            # 使用Blender将3DS转换为OBJ
            try:
                print("[INFO] 尝试使用Blender将3DS转换为OBJ...")
                
                blender_path = None
                # 尝试常见的Blender安装路径
                for path in [
                    "blender",  # 如果在PATH中
                    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
                    r"/Applications/Blender.app/Contents/MacOS/Blender",
                    r"/usr/bin/blender"
                ]:
                    try:
                        subprocess.run([path, "--version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
                        blender_path = path
                        break
                    except:
                        continue
                
                if not blender_path:
                    print("[WARNING] 找不到Blender可执行文件")
                    return False
                
                # 创建Blender脚本
                blender_script = os.path.join(os.path.dirname(input_path), "temp_blender_obj.py")
                with open(blender_script, 'w') as f:
                    f.write('import bpy\n')
                    f.write('bpy.ops.wm.read_factory_settings(use_empty=True)\n')
                    f.write('bpy.ops.import_scene.autodesk_3ds(filepath=r"%s")\n' % input_path.replace('\\', '\\\\'))
                    f.write('bpy.ops.export_scene.obj(filepath=r"%s")\n' % temp_obj.replace('\\', '\\\\'))
                
                # 执行Blender脚本
                subprocess.run([blender_path, "--background", "--python", blender_script], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                
                # 删除临时脚本
                if os.path.exists(blender_script):
                    os.remove(blender_script)
                
                # 检查临时文件是否成功创建
                if not os.path.exists(temp_obj) or os.path.getsize(temp_obj) == 0:
                    print("[ERROR] 临时OBJ文件创建失败")
                    return False
                    
                print(f"[INFO] 已创建临时OBJ文件: {temp_obj}")
            except Exception as e:
                print(f"[ERROR] 3DS到OBJ转换失败: {str(e)}")
                return False
            
            # 现在使用FreeCAD导入OBJ并导出为STL
            try:
                # 创建一个新文档
                doc = FreeCAD.newDocument("ThreeDStoSTL")
                print(f"[INFO] 创建FreeCAD文档: ThreeDStoSTL")
                
                # 导入OBJ文件
                try:
                    try:
                        import ImportObj
                        ImportObj.insert(temp_obj, doc.Name)
                    except ImportError:
                        print("[WARNING] ImportObj模块不可用，尝试其他导入方法")
                        # 如果ImportObj不可用，尝试使用Mesh.insert
                        Mesh.insert(temp_obj, doc.Name)
                except Exception as imp_err:
                    print(f"[ERROR] 导入OBJ文件失败: {str(imp_err)}")
                    raise
                
                # 检查是否成功导入
                if len(doc.Objects) == 0:
                    print("[ERROR] 导入OBJ文件失败，未创建任何对象")
                    FreeCAD.closeDocument(doc.Name)
                    os.remove(temp_obj)
                    return False
                
                # 获取所有可导出的网格对象
                mesh_objects = []
                for obj in doc.Objects:
                    if hasattr(obj, "Mesh") and obj.Mesh:
                        mesh_objects.append(obj)
                    elif hasattr(obj, "Shape") and obj.Shape:
                        # 如果是形状对象，转换为网格
                        try:
                            import MeshPart
                            mesh = MeshPart.meshFromShape(obj.Shape)
                            mesh_objects.append(mesh)
                        except ImportError:
                            print("[WARNING] MeshPart模块不可用，跳过形状对象转换")
                
                if not mesh_objects:
                    print("[ERROR] 未找到可导出的网格对象")
                    FreeCAD.closeDocument(doc.Name)
                    os.remove(temp_obj)
                    return False
                
                # 导出为STL
                output_format = "ASCII" if ascii_format else "Binary"
                print(f"[INFO] 导出为STL格式: {output_format}")
                
                try:
                    Mesh.export(mesh_objects, output_path, output_format)
                except Exception as exp_err:
                    print(f"[ERROR] 导出STL失败: {str(exp_err)}")
                    raise
                
                # 关闭文档和清理临时文件
                FreeCAD.closeDocument(doc.Name)
                os.remove(temp_obj)
                
                # 验证输出文件
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print("[INFO] FreeCAD导出STL成功")
                    return True
                else:
                    print("[ERROR] 导出STL文件失败或文件为空")
                    return False
                    
            except Exception as e:
                print(f"[ERROR] FreeCAD处理失败: {str(e)}")
                # 清理资源
                try:
                    if 'doc' in locals():
                        FreeCAD.closeDocument(doc.Name)
                except:
                    pass
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
                return False
                
        except Exception as e:
            print(f"[ERROR] FreeCAD转换过程出错: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            
            # 确保清理资源
            try:
                if 'doc' in locals():
                    FreeCAD.closeDocument(doc.Name)
            except:
                pass
            if 'temp_obj' in locals() and os.path.exists(temp_obj):
                os.remove(temp_obj)
                
            return False
    
    def input_format(self):
        return "3ds"
    
    def output_format(self):
        return "stl"


from api.utils.file_utils import add_random_prefix
import shutil

# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与3DS转换测试")
    print("=" * 50)
    
    # 测试STL到3DS转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    
    # 测试添加红色
    print(f"[INFO] 测试STL到3DS转换")
    converter = STLTo3DSConverter()
    success, threeds_path = converter.convert(input_file_path, color=[255, 0, 0])
    print(f"[RESULT] STL到3DS转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试3DS到STL转换
        print(f"[INFO] 测试3DS到STL转换，使用二进制格式")
        converter = ThreeDSToSTLConverter()
        success, stl_path = converter.convert(threeds_path)
        print(f"[RESULT] 3DS到STL(二进制)转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试3DS到STL ASCII转换
            print(f"[INFO] 测试3DS到STL转换，使用ASCII格式")
            converter = ThreeDSToSTLConverter()
            success, stl_ascii_path = converter.convert(threeds_path, ascii=True)
            print(f"[RESULT] 3DS到STL(ASCII)转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
