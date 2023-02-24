import os
import time
import argparse

from functions import *

save_artefacts = True
padding_out = 60
img_upscale = 3
img_blur = img_upscale
threshold = 150

if __name__ == "__main__":
    dir_pass("temp")

    parser = argparse.ArgumentParser(
        description="Convert all instances of a word in a PDF to a video.")

    parser.add_argument(
        "-f", "--file", type=str, help="File path (only PDF is supported as of now)", metavar="", required=True)

    parser.add_argument(
        "-w", "--word", type=str, help="The word you want to make video of", metavar="", required=True)

    parser.add_argument(
        "-i", "--intermediate", type=bool, help="Save intermediate artefacts [location='temp/'] (default=False)", metavar="", default=False)

    parser.add_argument(
        "-p", "--padding", type=int, help="Extent of outside visible box in px (default=60px)", metavar="", default=60)

    parser.add_argument(
        "-u", "--upscale", type=int, help="Image upscaling factor (default=3)", metavar="", default=3)

    parser.add_argument(
        "-r", "--framerate", type=int, help="Framerate of output video (default=10)", metavar="", default=10)

    parser.add_argument(
        "-o", "--output", type=str, help="Output file name. Located at \"outs/<filename>/<word>.mp4\"", metavar="", required=False)

    args = parser.parse_args()

    loc = args.file
    to_find = args.word
    save_artefacts = args.intermediate
    padding_out = args.padding
    img_upscale = args.upscale
    framerate = args.framerate
    out_ = f"outs/{get_filename(loc)}_{to_find}.mp4"

    print("Extracting pages from PDF")
    pages_cv, pages_np = get_pages(loc)
    print("*"*30)

    # all_words = []
    for page_no, (page_cv, page_np) in enumerate(zip(pages_cv, pages_np)):
        print(f"Extracting words from page {page_no+1}")
        final_word_images = get_final_word_images(page_cv, page_np)
        # all_words += final_word_images

        print(f"Saving frames to disk for page {page_no+1}")
        write_all_instances_to_disk(
            final_word_images, get_filename(loc)+"/"+to_find, page_no)
        print("*"*30)
        time.sleep(0.5)

    in_ = "temp/word_images/"+get_filename(loc)+"/"+to_find+"/*.png"

    out_ = "outs/"+get_filename(loc)+"/"+to_find+".mp4"
    dir_pass(out_.rsplit("/", 1)[0])

    command = f"ffmpeg -framerate {framerate} -pattern_type glob -i '{in_}' -c:v libx264 {out_} -y"
    os.system(command)
