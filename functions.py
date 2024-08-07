import os
import time


from pdf2image import convert_from_path
from pytesseract import pytesseract
import cv2 as cv
import numpy as np
from scipy.ndimage import gaussian_filter

save_artefacts = True
padding_out = 60
img_upscale = 3
img_blur = img_upscale
threshold = 150

loc = None
to_find = None
save_artefacts = None
padding_out = None
img_upscale = None
framerate = None

def dir_pass(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]


def save_pages(pages, root_name):
    path = "temp/page_images/" + root_name
    dir_pass(path)
    for index, page in enumerate(pages):
        cv.imwrite(path+"/temp_"+str(index)+".png", page)
        time.sleep(0.1)


def get_pages(path):
    pages = convert_from_path(path, 300)
    pages_cv = [page.convert('L') for page in pages]
    pages_np = [np.asarray(page) for page in pages_cv]
    if save_artefacts:
        save_pages(pages_np, get_filename(path))
    return pages_cv, pages_np


def get_all_data(page):
    data = pytesseract.image_to_boxes(page).strip().split("\n")
    data = [k.split(" ")[1:-1] for k in data]
    data = [[int(t) for t in k] for k in data]
    text = pytesseract.image_to_string(page).strip().replace("\n", " ")
    return data, text


def normalize_data(data, text):
    mapped_input = []
    ind_data = 0
    for letter in text:
        if letter != " ":
            mapped_input += [letter, data[ind_data]],
            ind_data += 1
            continue
        mapped_input += [letter, [0, 0, 0, 0]],
    return mapped_input


def normalize_coordinates(data, height):
    new_data = []
    for datum in data:
        new_data += [datum[0], [datum[1][0], height -
                                datum[1][3], datum[1][2], height - datum[1][1]]],
    return new_data


def get_word_boundary(data):
    if not len(data):
        return None, None
    word = "".join([k[0] for k in data])
    boundaries = np.array([k[1] for k in data]).T
    temp_bound = [min(boundaries[0])-10, min(boundaries[1])-10,
                  max(boundaries[2])+10, max(boundaries[3])+10]
    return word.lower(), temp_bound


def merge_words(data):
    new_data = {}
    temp = []
    for dat in data:
        if dat[0] == " ":
            word, boundary = get_word_boundary(temp)
            if word:
                if word not in new_data:
                    new_data[word] = []
                new_data[word] += boundary,
            temp = []
            continue
        if dat[0] in [".", ",", "“", "”"]:
            continue
        temp += dat,
    return new_data


def process_page(page_cv, page_np):
    raw_data = get_all_data(page_cv)
    full_split_data = normalize_data(*raw_data)
    normalized = normalize_coordinates(full_split_data, page_np.shape[0])
    merged = merge_words(normalized)
    return merged


def get_all_instances_as_img(merged, word, img):
    stack = []
    if word not in merged:
        return stack
    locs = []
    for page_word in merged:
        if word in page_word:
            locs += merged[page_word]
    for box in locs:
        base = np.copy(img[box[1]-padding_out:box[3] +
                           padding_out, box[0]-padding_out:box[2]+padding_out])
        base = np.kron(base, np.ones((img_upscale, img_upscale)))
        base = gaussian_filter(base, sigma=img_blur)
        current = np.copy(base[padding_out*img_upscale:-padding_out *
                               img_upscale, padding_out*img_upscale:-padding_out*img_upscale])
        current[current <= threshold] = 0
        current[current > threshold] = 255
        base[padding_out*img_upscale:-padding_out * img_upscale,
             padding_out*img_upscale:-padding_out*img_upscale] = current
        stack += base,
    return stack


def write_all_instances_to_disk(arr, name, page):
    root = "temp/word_images/"+name+"/"
    dir_pass(root)
    for index, k in enumerate(arr):
        cv.imwrite(f"{root}{page:03}_{index:03}.png", k)


def get_final_word_images(page_cv, page_np):
    merged = process_page(page_cv, page_np)
    temp = get_all_instances_as_img(merged, to_find, page_np)
    if not len(temp):
        return []
    shapes = np.array([k.shape for k in temp])
    x, y = np.min(shapes, axis=0)
    x -= x % 2
    y -= y % 2
    final_planes = []
    for instance in temp:
        X, Y = instance.shape
        dx = int((X-x)/2)
        dy = int((Y-y)/2)
        final_planes += instance[dx:-dx-1, dy:-dy-1][:x-1, :y-1],
    return final_planes

