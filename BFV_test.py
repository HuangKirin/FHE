import os
import numpy as np
import tenseal as ts
from PIL import Image
from time import time

def encrypt_and_save_image(context, image_array, folder_path, file_name):
    encryption_start = time()
    encrypted_data = ts.bfv_vector(context, image_array.flatten())
    encryption_end = time()
    print(f"第{i}张图像加密时间：{((encryption_end - encryption_start)*1000)}")

    encrypted_data_path = os.path.join(folder_path, file_name + ".bin")
    
    with open(encrypted_data_path, "wb") as f:
        f.write(encrypted_data.serialize())

def load_encrypted_image(folder_path, file_name, context):
    encrypted_data_path = os.path.join(folder_path, file_name + ".bin")
    
    with open(encrypted_data_path, "rb") as f:
        encrypted_data = ts.bfv_vector_from(context, f.read())
    
    return encrypted_data

def calculate_mse(encrypted_data1, encrypted_data2):
    # 在加密状态下执行操作：(encrypted_data1 - encrypted_data2)^2
    result_subtraction = encrypted_data1.sub(encrypted_data2)
    mse = result_subtraction * result_subtraction
    mse = mse.decrypt()
    mse = np.array(mse)
    mse = np.mean(mse)
    return mse

def fuzzy_match(context, query, data_folder):
    query_start = time()

    min_mse = float('inf')  # 初始化为正无穷大
    min_mse_filename = None

    mse_values = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".bin"):
            encrypted_data = load_encrypted_image(data_folder, filename[:-4], context)

            # 记录加密开始时间
            encryption_start = time()

            mse = calculate_mse(query, encrypted_data)

            # 记录加密结束时间
            encryption_end = time()

            mse_values.append((filename[:-4], mse, encryption_end - encryption_start))

            # 如果 decrypted_mse 更小，则更新 min_mse
            if mse < min_mse:
                min_mse = mse
                min_mse_filename = filename[:-4]
            # 输出格式化字符串
            print("加密图像：{:<20}  MSE：{:<15.6f}  查询时间：{:<15.6f}".format(
                filename[:-4], mse, (encryption_end - encryption_start) * 1000))

    query_end = time()

    if min_mse_filename is not None:
        print(f"\n最佳匹配图像: {min_mse_filename}, 最小MSE: {min_mse}")
    else:
        print("\n没有找到匹配的加密图像")

    print("\n匹配时间: {:.6f} 毫秒".format((query_end - query_start) * 1000))

# 创建加密上下文
context = ts.context(ts.SCHEME_TYPE.BFV, poly_modulus_degree=8192, plain_modulus=1032193)

# 设置文件夹路径并创建目录
script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
encrypted_images_folder = os.path.join(script_directory, "encrypted_images")
os.makedirs(encrypted_images_folder, exist_ok=True)

script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
images_folder = os.path.join(script_directory, "images")

image_paths = [os.path.join(images_folder, filename) for filename in os.listdir(images_folder) if filename.endswith(".PNG")]

for i, image_path in enumerate(image_paths, start=1):
    original_image = Image.open(image_path)
    resized_image = original_image.resize((64, 64))
    image_array = np.array(resized_image)
    encrypt_and_save_image(context, image_array, encrypted_images_folder, f"encrypted_image_{i}")

# 加密查询图像
query_image_path = r"images\1.PNG"
query_original_image = Image.open(query_image_path)
query_resized_image = query_original_image.resize((64, 64))
query_image_array = np.array(query_resized_image)
query_encrypted_data = ts.bfv_vector(context, query_image_array.flatten())

# 执行带有MSE阈值的模糊匹配
fuzzy_match(context, query_encrypted_data, encrypted_images_folder)
