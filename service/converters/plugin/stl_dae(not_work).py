import sys
from service.converters.base import BaseConverter
import trimesh
import os
import time
import numpy as np
import subprocess

#未实现
class STLToDAEConverter(BaseConverter):
    """将STL文件转换为DAE(Collada)文件的转换器"""
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将STL文件转换为DAE文件
        
        参数:
            input_path: STL文件路径
            output_path: 输出DAE文件路径，如果为None则自动生成
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
            output_path = os.path.join(input_dir, f"{input_basename}.dae")
            print(f"[INFO] 未提供输出路径，自动生成: {output_path}")
        
        print(f"[INFO] 开始STL到DAE转换: {input_path} -> {output_path}")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 在尝试其他方法之前，先尝试直接使用trimesh进行转换
            print("[INFO] 尝试使用trimesh直接转换...")
            try:
                # 加载STL文件
                mesh = trimesh.load(input_path)
                
                # 如果提供了颜色参数，为模型添加颜色
                if default_color is not None:
                    try:
                        if len(default_color) >= 3 and all(0 <= c <= 255 for c in default_color[:3]):
                            color_norm = [c/255.0 for c in default_color[:3]]
                            colors = np.ones((len(mesh.faces), 4))
                            colors[:, 0:3] = color_norm
                            mesh.visual.face_colors = colors
                            print(f"[INFO] 已应用默认颜色: RGB{default_color[:3]}")
                    except Exception as e:
                        print(f"[WARNING] 设置颜色失败: {str(e)}")
                
                # 直接导出为DAE
                mesh.export(output_path, file_type='collada')
                
                # 验证输出文件
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    output_size = os.path.getsize(output_path) / 1024.0
                    print(f"[INFO] DAE文件导出成功: {output_size:.2f} KB")
                    return True, output_path
                else:
                    print("[WARNING] trimesh直接导出失败，尝试其他方法...")
            except Exception as e:
                print(f"[WARNING] trimesh直接转换失败: {str(e)}，尝试其他方法...")
            
            # 尝试使用FreeCAD进行转换
            success = self._try_freecad_conversion(input_path, output_path)
            if success:
                # 验证输出文件
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    output_size = os.path.getsize(output_path) / 1024.0
                    print(f"[INFO] DAE文件导出成功: {output_size:.2f} KB")
                    
                    end_time = time.time()
                    print(f"[INFO] STL到DAE转换完成! 用时: {end_time - start_time:.2f} 秒")
                    print(f"[SUCCESS] 转换为DAE成功: {output_path}")
                    return True, output_path
                else:
                    print("[WARNING] FreeCAD转换完成但未生成有效文件，尝试其他方法...")
            else:
                print("[INFO] FreeCAD转换不可用，尝试其他方法...")
            
            # 尝试使用中间格式（OBJ）作为转换桥梁
            print("[INFO] 通过OBJ中间格式进行转换...")
            temp_obj = os.path.join(os.path.dirname(input_path), f"temp_{os.path.basename(input_path)}.obj")
            
            try:
                # 导出为OBJ中间格式
                mesh.export(temp_obj, file_type='obj')
                print(f"[INFO] 已创建临时OBJ文件: {temp_obj}")
                
                # 方法1: 尝试使用Assimp库（通过PyAssimp）
                try:
                    print("[INFO] 尝试使用PyAssimp...")
                    try:
                        import pyassimp
                        scene = pyassimp.load(temp_obj)
                        pyassimp.export(scene, output_path, file_type='collada')
                        pyassimp.release(scene)
                        print("[INFO] PyAssimp转换成功")
                        
                        # 验证输出文件
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            success = True
                        else:
                            raise Exception("PyAssimp导出文件无效")
                    except ImportError as imp_err:
                        print(f"[WARNING] PyAssimp不可用: {str(imp_err)}")
                        raise Exception("PyAssimp不可用")
                    except Exception as assimp_err:
                        print(f"[WARNING] PyAssimp转换失败: {str(assimp_err)}")
                        raise Exception(f"PyAssimp转换失败: {str(assimp_err)}")
                        
                except Exception as e:
                    print(f"[WARNING] Assimp方法失败: {str(e)}")
                    
                    # 方法2: 安全使用pymeshlab（在单独进程中）
                    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                        print("[INFO] 尝试使用pymeshlab（安全模式）...")
                        
                        # 创建一个临时Python脚本来执行pymeshlab操作
                        temp_script = os.path.join(os.path.dirname(input_path), "temp_pymeshlab_dae.py")
                        
                        with open(temp_script, 'w') as f:
                            f.write('import sys\n')
                            f.write('try:\n')
                            f.write('    import pymeshlab\n')
                            f.write('    ms = pymeshlab.MeshSet()\n')
                            f.write(f'    ms.load_new_mesh("{temp_obj}")\n')
                            f.write(f'    ms.save_current_mesh("{output_path}")\n')
                            f.write('    print("SUCCESS")\n')
                            f.write('except Exception as e:\n')
                            f.write('    print(f"ERROR: {e}")\n')
                        
                        # 在单独的进程中执行脚本
                        try:
                            result = subprocess.run([sys.executable, temp_script], 
                                                  capture_output=True, text=True, timeout=30)
                            
                            # 检查结果
                            if "SUCCESS" in result.stdout:
                                print("[INFO] pymeshlab安全模式转换成功")
                            else:
                                print(f"[WARNING] pymeshlab安全模式失败: {result.stdout}")
                                raise Exception("pymeshlab处理失败")
                                
                            # 删除临时脚本
                            if os.path.exists(temp_script):
                                os.remove(temp_script)
                                
                        except subprocess.TimeoutExpired:
                            print("[WARNING] pymeshlab处理超时")
                            if os.path.exists(temp_script):
                                os.remove(temp_script)
                            raise Exception("pymeshlab处理超时")
                            
                        except Exception as subproc_err:
                            print(f"[WARNING] 子进程执行失败: {str(subproc_err)}")
                            if os.path.exists(temp_script):
                                os.remove(temp_script)
                            raise Exception(f"子进程执行失败: {str(subproc_err)}")
                    
                    # 方法3: 直接使用Blender（如果可用）
                    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
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
                            blender_script = os.path.join(os.path.dirname(input_path), "temp_blender.py")
                            with open(blender_script, 'w') as f:
                                f.write('import bpy\n')
                                f.write('bpy.ops.wm.read_factory_settings(use_empty=True)\n')
                                f.write('bpy.ops.import_scene.obj(filepath=r"%s")\n' % temp_obj.replace('\\', '\\\\'))
                                f.write('bpy.ops.wm.collada_export(filepath=r"%s")\n' % output_path.replace('\\', '\\\\'))
                            
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
                
                # 删除临时OBJ文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
                    print("[INFO] 删除临时OBJ文件")
                
            except Exception as obj_err:
                print(f"[WARNING] OBJ中间格式转换失败: {str(obj_err)}")
                # 确保删除临时文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] DAE文件导出成功: {output_size:.2f} KB")
                
                end_time = time.time()
                print(f"[INFO] STL到DAE转换完成! 用时: {end_time - start_time:.2f} 秒")
                print(f"[SUCCESS] 转换为DAE成功: {output_path}")
                return True, output_path
            else:
                print("[ERROR] 导出失败: 输出文件未创建或为空")
                return False, None
                
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] STL到DAE转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def _try_freecad_conversion(self, input_path, output_path):
        """
        尝试使用FreeCAD直接进行STL到DAE的转换
        使用FreeCAD API而不是子进程
        """
        print("[INFO] 尝试使用FreeCAD进行转换...")
        
        try:
            # 尝试直接导入FreeCAD模块
            try:
                import FreeCAD
                import Mesh
                import Part
                print("[INFO] 成功导入FreeCAD模块")
            except ImportError:
                print("[WARNING] 无法导入FreeCAD模块，FreeCAD可能未安装或未添加到Python路径")
                return False
            
            # 设置FreeCAD无GUI模式
            import os
            os.environ["FREECAD_NO_GUI"] = "1"
            
            # 创建一个新文档
            doc = FreeCAD.newDocument("STLtoDAE")
            print(f"[INFO] 创建FreeCAD文档: STLtoDAE")
            
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
            
            # 尝试直接导出为DAE
            print(f"[INFO] 尝试直接导出为DAE: {output_path}")
            try:
                # 根据FreeCAD控制台输出修改导入路径
                try:
                    import importers.importDAE
                    print("[INFO] 使用importers.importDAE模块导出...")
                    # 创建要导出的对象列表
                    export_objs = [mesh_obj]
                    
                    # 检查是否有导出选项
                    if hasattr(importers.importDAE, "exportOptions"):
                        options = importers.importDAE.exportOptions(output_path)
                        importers.importDAE.export(export_objs, output_path, options)
                    else:
                        importers.importDAE.export(export_objs, output_path)
                        
                    # 检查文件是否已创建
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"[INFO] DAE文件导出成功: {output_path}")
                        FreeCAD.closeDocument(doc.Name)
                        return True
                        
                except ImportError as e:
                    print(f"[WARNING] 无法导入importers.importDAE: {e}")
                    # 尝试其他可能的导入路径
                    try_paths = [
                        "importDAE",
                        "Import.importDAE"
                    ]
                    
                    success = False
                    for module_path in try_paths:
                        try:
                            print(f"[INFO] 尝试导入模块: {module_path}")
                            module = __import__(module_path, fromlist=["export"])
                            
                            # 创建要导出的对象列表
                            export_objs = [mesh_obj]
                            
                            # 检查是否有导出选项
                            if hasattr(module, "exportOptions"):
                                options = module.exportOptions(output_path)
                                module.export(export_objs, output_path, options)
                            else:
                                module.export(export_objs, output_path)
                                
                            # 检查文件是否已创建
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                print(f"[INFO] 使用{module_path}成功导出DAE文件")
                                success = True
                                break
                        except Exception as import_err:
                            print(f"[WARNING] {module_path}导入或导出失败: {import_err}")
                    
                    if not success:
                        # 如果所有模块都失败，尝试使用临时脚本导出
                        print("[INFO] 尝试使用临时脚本进行导出...")
                        temp_script = os.path.join(os.path.dirname(output_path), "freecad_export_dae.py")
                        with open(temp_script, 'w') as f:
                            f.write('import sys\n')
                            f.write('import os\n')
                            f.write('import FreeCAD\n')
                            f.write('import Mesh\n')
                            f.write(f'doc = FreeCAD.open("{input_path}")\n')
                            f.write('objs = doc.Objects\n')
                            f.write('try:\n')
                            f.write('    # 尝试多种可能的导入方式\n')
                            f.write('    try:\n')
                            f.write('        import importers.importDAE\n')
                            f.write('        if hasattr(importers.importDAE, "exportOptions"):\n')
                            f.write(f'            options = importers.importDAE.exportOptions("{output_path}")\n')
                            f.write(f'            importers.importDAE.export(objs, "{output_path}", options)\n')
                            f.write('        else:\n')
                            f.write(f'            importers.importDAE.export(objs, "{output_path}")\n')
                            f.write('        print("SUCCESS")\n')
                            f.write('    except ImportError:\n')
                            f.write('        try:\n')
                            f.write('            import importDAE\n')
                            f.write('            if hasattr(importDAE, "exportOptions"):\n')
                            f.write(f'                options = importDAE.exportOptions("{output_path}")\n')
                            f.write(f'                importDAE.export(objs, "{output_path}", options)\n')
                            f.write('            else:\n')
                            f.write(f'                importDAE.export(objs, "{output_path}")\n')
                            f.write('            print("SUCCESS")\n')
                            f.write('        except ImportError:\n')
                            f.write('            try:\n')
                            f.write('                from Import import importDAE\n')
                            f.write(f'                if hasattr(importDAE, "exportOptions"):\n')
                            f.write(f'                    options = importDAE.exportOptions("{output_path}")\n')
                            f.write(f'                    importDAE.export(objs, "{output_path}", options)\n')
                            f.write('                else:\n')
                            f.write(f'                    importDAE.export(objs, "{output_path}")\n')
                            f.write('                print("SUCCESS")\n')
                            f.write('            except Exception as e:\n')
                            f.write('                print(f"ERROR: {e}")\n')
                            f.write('except Exception as e:\n')
                            f.write('    print(f"ERROR: {e}")\n')
                            f.write('finally:\n')
                            f.write('    FreeCAD.closeDocument(doc.Name)\n')
                        
                        try:
                            # 运行临时脚本
                            import sys
                            result = subprocess.run([sys.executable, temp_script], 
                                                  capture_output=True, text=True, timeout=60)
                            
                            # 检查结果
                            print(f"[INFO] 临时脚本输出: {result.stdout}")
                            if "SUCCESS" in result.stdout:
                                print("[INFO] 临时脚本成功导出DAE文件")
                                # 检查文件是否已创建
                                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                    success = True
                        except Exception as script_err:
                            print(f"[ERROR] 运行临时脚本失败: {script_err}")
                        finally:
                            # 删除临时脚本
                            if os.path.exists(temp_script):
                                os.remove(temp_script)
                    
                    if not success:
                        # 如果直接导出失败，尝试中间格式转换
                        return self._try_freecad_intermediate_conversion(input_path, output_path, mesh_obj, doc)
                        
            except Exception as direct_export_err:
                print(f"[ERROR] 直接导出DAE失败: {direct_export_err}")
                # 尝试中间格式转换
                return self._try_freecad_intermediate_conversion(input_path, output_path, mesh_obj, doc)
            
            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            print("[INFO] 关闭FreeCAD文档")
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[INFO] DAE文件导出成功: {output_path}")
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
            
            return False

    def _try_freecad_intermediate_conversion(self, input_path, output_path, mesh_obj, doc):
        """使用中间格式进行FreeCAD转换"""
        print("[INFO] 尝试通过中间格式进行转换...")
        try:
            import os
            import FreeCAD
            import Mesh
            
            # 创建临时OBJ文件路径
            temp_obj = input_path + ".temp.obj"
            print(f"[INFO] 创建临时OBJ文件: {temp_obj}")
            
            # 导出为OBJ格式
            Mesh.export([mesh_obj], temp_obj)
            
            # 检查临时文件是否成功创建
            if not os.path.exists(temp_obj) or os.path.getsize(temp_obj) == 0:
                print("[ERROR] 临时OBJ文件创建失败")
                FreeCAD.closeDocument(doc.Name)
                return False
            
            # 创建一个新文档用于导入OBJ并导出DAE
            import_doc = FreeCAD.newDocument("ImportObj")
            try:
                # 导入OBJ
                try:
                    import ImportObj
                    ImportObj.insert(temp_obj, import_doc.Name)
                except ImportError:
                    # 尝试其他可能的导入方式
                    try:
                        import importOBJ
                        importOBJ.insert(temp_obj, import_doc.Name)
                    except ImportError:
                        try:
                            import Import.importOBJ
                            Import.importOBJ.insert(temp_obj, import_doc.Name)
                        except ImportError:
                            print("[ERROR] 无法导入OBJ文件，未找到导入模块")
                            raise
                
                # 检查是否成功导入
                if len(import_doc.Objects) == 0:
                    print("[ERROR] 导入OBJ文件失败，未创建任何对象")
                    raise Exception("导入OBJ文件失败")
                
                # 尝试导出为DAE
                print(f"[INFO] 从中间OBJ文件导出为DAE: {output_path}")
                try:
                    # 尝试各种可能的导出模块
                    try:
                        import importers.importDAE
                        if hasattr(importers.importDAE, "exportOptions"):
                            options = importers.importDAE.exportOptions(output_path)
                            importers.importDAE.export(import_doc.Objects, output_path, options)
                        else:
                            importers.importDAE.export(import_doc.Objects, output_path)
                    except ImportError:
                        try:
                            import importDAE
                            if hasattr(importDAE, "exportOptions"):
                                options = importDAE.exportOptions(output_path)
                                importDAE.export(import_doc.Objects, output_path, options)
                            else:
                                importDAE.export(import_doc.Objects, output_path)
                        except ImportError:
                            try:
                                from Import import importDAE
                                if hasattr(importDAE, "exportOptions"):
                                    options = importDAE.exportOptions(output_path)
                                    importDAE.export(import_doc.Objects, output_path, options)
                                else:
                                    importDAE.export(import_doc.Objects, output_path)
                            except Exception as e:
                                print(f"[ERROR] 所有DAE导出模块尝试均失败: {e}")
                                raise
                except Exception as export_err:
                    print(f"[ERROR] 导出DAE失败: {export_err}")
                    raise
                
            except Exception as e:
                print(f"[ERROR] 中间OBJ处理失败: {e}")
                return False
            finally:
                # 关闭导入文档
                FreeCAD.closeDocument(import_doc.Name)
                # 删除临时OBJ文件
                if os.path.exists(temp_obj):
                    os.remove(temp_obj)
                    print("[INFO] 删除临时OBJ文件")
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[INFO] DAE文件导出成功通过中间格式: {output_path}")
                return True
            else:
                print("[ERROR] 导出DAE文件不存在或为空")
                return False
            
        except Exception as e:
            print(f"[ERROR] 中间格式转换失败: {e}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            
            # 删除临时文件
            if 'temp_obj' in locals() and os.path.exists(temp_obj):
                os.remove(temp_obj)
            
            return False

    def input_format(self):
        return "stl"

    def output_format(self):
        return "dae"

    def _convert_with_trimesh(self, input_path, output_path, default_color=None):
        """使用trimesh直接进行转换"""
        try:
            # 加载STL文件
            mesh = trimesh.load(input_path)
            print(f"[INFO] 成功加载STL网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            
            # 应用颜色（如果提供）
            if default_color is not None:
                try:
                    if len(default_color) >= 3 and all(0 <= c <= 255 for c in default_color[:3]):
                        color_norm = [c/255.0 for c in default_color[:3]]
                        colors = np.ones((len(mesh.faces), 4))
                        colors[:, 0:3] = color_norm
                        mesh.visual.face_colors = colors
                        print(f"[INFO] 已应用默认颜色: RGB{default_color[:3]}")
                except Exception as e:
                    print(f"[WARNING] 设置颜色失败: {str(e)}")
            
            # 直接导出为DAE
            mesh.export(output_path, file_type='collada')
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] DAE文件导出成功: {output_size:.2f} KB")
                return True
            return False
        except Exception as e:
            print(f"[WARNING] trimesh直接转换失败: {str(e)}")
            return False


class DAEToSTLConverter(BaseConverter):
    """将DAE(Collada)文件转换为STL文件的转换器"""
    
    def convert(self, input_path: str, output_path: str = None, **kwargs):
        """
        将DAE文件转换为STL文件
        
        参数:
            input_path: DAE文件路径
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
        print(f"[INFO] 开始DAE到STL转换: {input_path} -> {output_path} (格式: {'ASCII' if ascii_format else '二进制'})")
        start_time = time.time()
        
        try:
            # 记录输入文件信息
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path) / 1024.0
                print(f"[INFO] 输入文件大小: {file_size:.2f} KB")
            else:
                print(f"[ERROR] 输入文件不存在: {input_path}")
                return False, None
                
            # 尝试直接使用trimesh加载
            print("[INFO] 尝试加载DAE文件...")
            try:
                # 尝试使用trimesh加载
                mesh = trimesh.load(input_path)
                print(f"[INFO] 成功加载DAE文件: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
            except Exception as direct_load_err:
                print(f"[WARNING] 直接加载DAE失败: {str(direct_load_err)}")
                
                # 尝试加载为场景，然后合并
                try:
                    print("[INFO] 尝试加载为场景并合并...")
                    scene = trimesh.load(input_path, force='scene')
                    
                    if isinstance(scene, trimesh.Scene):
                        # 从场景提取所有网格
                        meshes = []
                        for name, geometry in scene.geometry.items():
                            if isinstance(geometry, trimesh.Trimesh):
                                meshes.append(geometry)
                                print(f"[INFO] 提取网格: {name} ({len(geometry.faces)} 面)")
                        
                        if meshes:
                            # 如果有多个网格，合并它们
                            if len(meshes) > 1:
                                print(f"[INFO] 合并 {len(meshes)} 个网格...")
                                mesh = trimesh.util.concatenate(meshes)
                            else:
                                mesh = meshes[0]
                                
                            print(f"[INFO] 成功合并网格: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
                        else:
                            raise ValueError("场景中未找到有效网格")
                    else:
                        raise ValueError("未能加载为有效场景")
                        
                except Exception as scene_err:
                    print(f"[WARNING] 场景方法失败: {str(scene_err)}")
                    
                    # 最后尝试pymeshlab
                    try:
                        import pymeshlab
                        print("[INFO] 尝试使用pymeshlab...")
                        
                        # 创建临时文件路径
                        temp_obj = input_path + ".temp.obj"
                        
                        # 使用pymeshlab加载和导出
                        ms = pymeshlab.MeshSet()
                        ms.load_new_mesh(input_path)
                        ms.save_current_mesh(temp_obj)
                        
                        # 加载转换后的临时文件
                        mesh = trimesh.load(temp_obj)
                        print(f"[INFO] 通过pymeshlab成功加载: {len(mesh.faces)} 面, {len(mesh.vertices)} 顶点")
                        
                        # 删除临时文件
                        if os.path.exists(temp_obj):
                            os.remove(temp_obj)
                            
                    except ImportError:
                        print("[ERROR] pymeshlab不可用，无法完成转换")
                        return False, None
                    except Exception as pymesh_err:
                        print(f"[ERROR] pymeshlab处理失败: {str(pymesh_err)}")
                        return False, None
            
            # 检查是否包含颜色信息
            has_color = False
            has_texture = False
            
            try:
                if hasattr(mesh.visual, 'face_colors') and mesh.visual.face_colors is not None:
                    has_color = True
                    print("[INFO] 检测到DAE文件包含颜色信息，转换为STL将丢失这些信息")
                
                # 检查是否包含纹理信息
                if hasattr(mesh.visual, 'material') and mesh.visual.material is not None:
                    if hasattr(mesh.visual.material, 'image'):
                        has_texture = True
                        print("[INFO] 检测到DAE文件包含纹理信息，转换为STL将丢失这些信息")
            except:
                pass
            
            # 导出为STL文件
            print(f"[INFO] 正在导出为STL文件 (格式: {'ASCII' if ascii_format else '二进制'})...")
            
            if ascii_format:
                # ASCII格式STL
                try:
                    mesh.export(output_path, file_type='stl_ascii')
                except Exception as ascii_err:
                    print(f"[WARNING] ASCII导出失败，尝试二进制格式: {str(ascii_err)}")
                    mesh.export(output_path, file_type='stl')
            else:
                # 二进制格式STL (默认)
                mesh.export(output_path, file_type='stl')
            
            # 验证输出文件
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024.0
                print(f"[INFO] STL文件导出成功: {output_size:.2f} KB")
                if has_color or has_texture:
                    print("[INFO] 注意: 颜色和纹理信息未包含在STL文件中")
            else:
                print("[ERROR] 导出失败: 输出文件未创建")
                return False, None
                
            end_time = time.time()
            print(f"[INFO] DAE到STL转换完成! 用时: {end_time - start_time:.2f} 秒")
            print(f"[SUCCESS] 转换为STL成功: {output_path}")
            return True, output_path  # 返回成功状态和输出路径
            
        except Exception as e:
            end_time = time.time()
            print(f"[ERROR] DAE到STL转换失败: {str(e)}")
            import traceback
            print(f"[DEBUG] 异常详情: {traceback.format_exc()}")
            print(f"[INFO] 转换失败! 用时: {end_time - start_time:.2f} 秒")
            return False, None
    
    def input_format(self):
        return "dae"
    
    def output_format(self):
        return "stl"


from utils.file_utils import add_random_prefix
import shutil

# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("[INFO] 开始STL与DAE转换测试")
    print("=" * 50)
    
    # 测试STL到DAE转换
    input_file_path = "C:\\Users\\13016\\Downloads\\good.stl"
    copy_path = "C:\\Users\\13016\\Downloads\\good222.stl"
    shutil.copyfile(input_file_path, copy_path)
    input_file_path = add_random_prefix(copy_path)
    print("修改文件的名字为", input_file_path)
    
    # 测试添加红色
    print(f"[INFO] 测试STL到DAE转换")
    converter = STLToDAEConverter()
    success, dae_path = converter.convert(input_file_path, color=[255, 0, 0])
    print(f"[RESULT] STL到DAE转换结果: {'成功' if success else '失败'}")
    
    if success:
        print("-" * 40)
        # 测试DAE到STL转换
        print(f"[INFO] 测试DAE到STL转换，使用二进制格式")
        converter = DAEToSTLConverter()
        success, stl_path = converter.convert(dae_path)
        print(f"[RESULT] DAE到STL(二进制)转换结果: {'成功' if success else '失败'}")
        
        if success:
            print("-" * 40)
            # 测试DAE到STL ASCII转换
            print(f"[INFO] 测试DAE到STL转换，使用ASCII格式")
            converter = DAEToSTLConverter()
            success, stl_ascii_path = converter.convert(dae_path, ascii=True)
            print(f"[RESULT] DAE到STL(ASCII)转换结果: {'成功' if success else '失败'}")
    
    print("=" * 50)
    print("[INFO] 转换测试完成")
    print("=" * 50)
