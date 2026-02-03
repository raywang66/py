# AutoAnalyzer vs Analyze Button 对比分析

## 问题描述
用户报告：FolderWatcher 发现的新照片通过 AutoAnalyzer 分析，结果不正确。
而 Analyze 按钮的结果是对的。

## 代码对比

### Analyze 按钮 (CC_Main.py:146)
```python
image_rgb = self.processor._load_image(self.image_path)
point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)
```

### AutoAnalyzer (CC_AutoAnalyzer.py:88-89)
```python
image_rgb = self.processor._load_image(photo_path)
point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)
```

## 结论
**代码完全相同！** 两者都调用：
1. `processor._load_image()` - 加载图片
2. `processor.process_image(image_rgb, return_mask=True)` - 处理图片

## processor.process_image() 流程 (CC_SkinProcessor.py:216-240)
1. 加载图片 RGB
2. **调用 MediaPipe 面部检测** (`face_detector.detect_face_mask(image_rgb)`)
3. 应用形态学操作（可选）
4. 提取 HSL 点云
5. 降采样（如果需要）
6. 返回 point_cloud 和 mask

## 面部遮罩检测 (CC_SkinProcessor.py:89-143)
MediaPipe Face Mesh 检测过程：
1. 检测人脸地标点
2. 填充面部轮廓
3. **排除眼睛、眉毛、嘴唇**
4. 返回面部皮肤遮罩

## 可能的问题

### 1. ❌ Processor 实例不同？
- Analyze 按钮: 使用 `self.processor` (主线程)
- AutoAnalyzer: 接收 `self.processor` (传递给子线程)

**重点**: AutoAnalyzer 使用的是**同一个 processor 实例**！

### 2. ❌ 线程安全问题？
MediaPipe 的 FaceMesh 可能不是线程安全的！

查看 CC_SkinProcessor.py:189-191:
```python
if use_mediapipe and MEDIAPIPE_AVAILABLE:
    self.face_detector = CC_MediaPipeFaceDetector()
```

CC_MediaPipeFaceDetector:75-79:
```python
self.face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    min_detection_confidence=0.5
)
```

**问题**: FaceMesh 对象在主线程创建，但在 AutoAnalyzer 的子线程中使用！

## 🔴 根本原因
**MediaPipe FaceMesh 不是线程安全的！**

当多个线程同时访问同一个 FaceMesh 实例时，可能导致：
- 面部检测失败
- 返回错误的地标点
- 遮罩生成错误

## 解决方案

### 方案 1: 每个线程创建独立的 processor
AutoAnalyzer 应该创建自己的 CC_SkinProcessor 实例。

### 方案 2: 加锁保护
使用 threading.Lock 保护 processor 的访问。

### 方案 3: 检查是否真的没有面部检测
添加日志查看 AutoAnalyzer 是否真的调用了面部检测。

## 验证步骤
1. 在 CC_AutoAnalyzer.py:89 添加日志
2. 检查 mask.sum() 是否为 0（没有面部）
3. 对比 Analyze 按钮的 mask.sum()
