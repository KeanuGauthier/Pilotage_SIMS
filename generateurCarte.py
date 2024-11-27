import random
from PIL import Image, ImageDraw


def generate_map_image():
    width, height = 1920, 1080
    border_thickness = 10
    num_obstacles = 20
    obstacle_min_size = 30
    obstacle_max_size = 120

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        [(0, 0), (width - 1, height - 1)],
        outline="black",
        width=border_thickness
    )

    def does_overlap(new_obstacle, existing_obstacles):
        new_x1, new_y1, new_x2, new_y2 = new_obstacle
        for ex in existing_obstacles:
            ex_x1, ex_y1, ex_x2, ex_y2 = ex
            if not (new_x2 < ex_x1 or new_x1 > ex_x2 or new_y2 < ex_y1 or new_y1 > ex_y2):
                return True
        return False

    obstacles = []
    for _ in range(num_obstacles):
        while True:
            shape_type = random.choice(["rectangle", "circle"])
            x1 = random.randint(border_thickness, width - border_thickness - obstacle_max_size)
            y1 = random.randint(border_thickness, height - border_thickness - obstacle_max_size)
            size = random.randint(obstacle_min_size, obstacle_max_size)
            x2, y2 = x1 + size, y1 + size

            if does_overlap((x1, y1, x2, y2), obstacles):
                continue

            obstacles.append((x1, y1, x2, y2))

            if shape_type == "rectangle":
                draw.rectangle([x1, y1, x2, y2], fill="black")
            elif shape_type == "circle":
                draw.ellipse([x1, y1, x2, y2], fill="black")

            break

    image.save("map_image.png")
    print("Image saved as 'map_image.png'")


generate_map_image()