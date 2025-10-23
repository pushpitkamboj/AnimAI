from .chunks import chunking
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb
import uuid

from dotenv import load_dotenv
load_dotenv()

files_to_index = [
    ("manim_docs/Camera.py", "https://docs.manim.community/en/stable/_modules/manim/camera/camera.html"),
    ("manim_docs/Animation.py", "https://docs.manim.community/en/stable/_modules/manim/animation/animation.html"),
    ("manim_docs/mobject_frame.py", "https://docs.manim.community/en/stable/reference/manim.mobject.frame.html"),
    ("manim_docs/mobject_geometry_arc.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.arc.html"),
    ("manim_docs/mobject_geometry_boolean_ops.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.boolean_ops.html"),
    ("manim_docs/mobject_geometry_labelled.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.labeled.html"),
    ("manim_docs/mobject_geometry_line.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.line.html"),
    ("manim_docs/mobject_geometry_polygram.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.polygram.html"),
    ("manim_docs/mobject_geometry_shape_matchers.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.shape_matchers.html"),
    ("manim_docs/mobject_geometry_tips.py", "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.tips.html"), 
    ("manim_docs/mobject_graph.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graph.html"),
    ("manim_docs/mobject_graphing_coordinate_systems.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.coordinate_systems.html"),
    ("manim_docs/mobject_graphing_functions.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.functions.html"),
    ("manim_docs/mobject_graphing_number_line.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.number_line.html"),
    ("manim_docs/mobject_graphing_probability.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.probability.html"),
    ("manim_docs/mobject_graphing_scale.py", "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.scale.html"),
    ("manim_docs/mobject_matrix.py", "https://docs.manim.community/en/stable/reference/manim.mobject.matrix.html"),
    ("manim_docs/mobject_table.py", "https://docs.manim.community/en/stable/reference/manim.mobject.table.html"),
    ("manim_docs/mobject_text.py", "https://docs.manim.community/en/stable/reference/manim.mobject.text.html"),
    ("manim_docs/mobject_three_d_polyhedra.py", "https://docs.manim.community/en/stable/reference/manim.mobject.three_d.polyhedra.html"),
    ("manim_docs/mobject_three_d_three_d_utils.py", "https://docs.manim.community/en/stable/reference/manim.mobject.three_d.three_d_utils.html"), 
    ("manim_docs/mobject_three_d_three_dimensions.py", "https://docs.manim.community/en/stable/reference/manim.mobject.three_d.three_dimensions.html"),
    ("manim_docs/mobject_types_image_mobject.py", "https://docs.manim.community/en/stable/reference/manim.mobject.types.image_mobject.html"),
    ("manim_docs/mobject_types_point_cloud_mobject.py", "https://docs.manim.community/en/stable/reference/manim.mobject.types.point_cloud_mobject.html"),
    ("manim_docs/mobject_types_vectorized_mobject.py", "https://docs.manim.community/en/stable/reference/manim.mobject.types.vectorized_mobject.html"),
    ("manim_docs/mobject_value_tracker.py", "https://docs.manim.community/en/stable/reference/manim.mobject.value_tracker.html"),
    ("manim_docs/mobject_vector_field.py", "https://docs.manim.community/en/stable/reference/manim.mobject.vector_field.html"),
    ("manim_docs/scenes_moving_camera_scene.py", "https://docs.manim.community/en/stable/reference/manim.scene.moving_camera_scene.html"), #issue
    ("manim_docs/scenes_scene.py", "https://docs.manim.community/en/stable/reference/manim.scene.scene.html"),
    ("manim_docs/scenes_three_d_scene.py", "https://docs.manim.community/en/stable/reference/manim.scene.three_d_scene.html"),
    ("manim_docs/scenes_vector_space_scene.py", "https://docs.manim.community/en/stable/reference/manim.scene.vector_space_scene.html"),
    ("manim_docs/utils_color_core.py", "https://docs.manim.community/en/stable/reference/manim.utils.color.core.html"),
    ("manim_docs/utils_commands.py", "https://docs.manim.community/en/stable/reference/manim.utils.commands.html"), #issue
    ("manim_docs/utils_bezier.py", "https://docs.manim.community/en/stable/reference/manim.utils.bezier.html") #issue
]


ids = []
content = []
all_metadata = []

for file_path, metadata_url in files_to_index:
    final_chunks = chunking(file_path, metadata_url)
    parent_chunks = final_chunks[0]
    child_chunks = final_chunks[1]

    parents_metadata = []
    for item in parent_chunks:
        unique_id = str(uuid.uuid4())
        item_metadata = {
            "type": item["type"],
            "file_path": item["file_path"],
            "id": item["id"],
            "children_ids": ", ".join(item["children_ids"]),
        }
        
        ids.append(unique_id)
        content.append(item["content"])
        all_metadata.append(item_metadata)
        
    children_metadata = []
    for item in child_chunks:
        unique_id = str(uuid.uuid4())
        item_metadata = {
            "type": item["type"], 
            "file_path": item["file_path"],
            "id": item["id"], 
            "parent_id": item["parent_id"]
        }
        
        ids.append(unique_id)
        content.append(item["content"])
        all_metadata.append(item_metadata)
        

client = chromadb.CloudClient()

collection = client.get_collection(
    name="manim_source_code", 
    embedding_function=OpenAIEmbeddingFunction(
        model_name="text-embedding-3-small"
    )
)

# Note - do not process all the files at once, keep each batch size < 300
#around 145 parent class and 842 methods
#max classes- 16(mobject_geometry_arc)
#max objects - 127(mobject_types_vectorized_mobject)

# collection.add(ids=ids, documents=content, metadatas=all_metadata)
    
    

