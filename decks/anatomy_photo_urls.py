"""Remote anatomy images (Wikimedia Commons / OpenStax, CC BY).

Used when generating anatomy.json with --remote (default).
Run `python3 decks/resolve_anatomy_photos.py` to refresh URLs from Commons.
"""
from __future__ import annotations

# Thumbnails ~960px or original JPEG where smaller.
TOPIC_PHOTO_URLS: dict[str, list[str]] = {
    "Терминология и основы": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Directional_Terms.jpg/960px-Directional_Terms.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Regions_of_Human_Body.jpg/960px-Regions_of_Human_Body.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Organ_Systems_I.jpg/960px-Organ_Systems_I.jpg",
    ],
    "Опорно-двигательная": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Human_skeleton_front_en.svg/960px-Human_skeleton_front_en.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/c/ca/603_Anatomy_of_a_Long_Bone.jpg",
    ],
    "Мышцы": [
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/1002_Organization_of_Muscle_Fiber.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/1107_The_Extrinsic_Eye_Muscles.jpg/960px-1107_The_Extrinsic_Eye_Muscles.jpg",
    ],
    "Сердечно-сосудистая": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/2000_Human_Heart_Photo.jpg/960px-2000_Human_Heart_Photo.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/2005_Surface_Anatomy_of_the_Heart.jpg/960px-2005_Surface_Anatomy_of_the_Heart.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Circulatory_System_en.svg/960px-Circulatory_System_en.svg.png",
    ],
    "Дыхательная": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/2312_Gross_Anatomy_of_the_Lungs.jpg/960px-2312_Gross_Anatomy_of_the_Lungs.jpg",
    ],
    "Пищеварительная": [
        "https://upload.wikimedia.org/wikipedia/commons/0/03/2401_Components_of_the_Digestive_System.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/b/b7/2423_Microscopic_Anatomy_of_Liver.jpg",
    ],
    "Мочевыделительная": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2610_The_Kidney.jpg/960px-2610_The_Kidney.jpg",
    ],
    "Нервная система": [
        "https://upload.wikimedia.org/wikipedia/commons/1/1e/1207_Neuron_Shape_Classification.jpg",
    ],
    "Эндокринная": [
        "https://upload.wikimedia.org/wikipedia/commons/c/ca/1801_The_Endocrine_System_esp.jpg",
    ],
    "Органы чувств": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/1413_Structure_of_the_Eye.jpg/960px-1413_Structure_of_the_Eye.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/1404_The_Structures_of_the_Ear.jpg/960px-1404_The_Structures_of_the_Ear.jpg",
    ],
    "Покровная система": [
        "https://upload.wikimedia.org/wikipedia/commons/1/13/Human_skin_structure.jpg",
    ],
    "Лимфатическая": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/2201_Anatomy_of_the_Lymphatic_System.jpg/960px-2201_Anatomy_of_the_Lymphatic_System.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/2202_Lymphatic_Capillaries.jpg/960px-2202_Lymphatic_Capillaries.jpg",
    ],
    "Репродуктивная": [
        "https://upload.wikimedia.org/wikipedia/commons/4/4e/Figure_28_02_06.JPG",
        "https://upload.wikimedia.org/wikipedia/commons/5/53/Figure_28_01_02.JPG",
        "https://upload.wikimedia.org/wikipedia/commons/5/55/Figure_28_01_03.JPG",
    ],
    "Головной мозг": [
        "https://upload.wikimedia.org/wikipedia/commons/4/49/Human_brain_NIH.jpg",
    ],
    "Позвоночник": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/1313_Spinal_Cord_Cross_Section.jpg/960px-1313_Spinal_Cord_Cross_Section.jpg",
    ],
}
