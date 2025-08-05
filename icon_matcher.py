

canonical_icon_map = {
    "run": "run",
    "walk": "walk",
    "bike": "bike",
    "swim": "swim",
    "hike": "hiking",
    "camp": "tent",
    "fish": "fish",
    "bird": "bird",
    "garden": "flower",
    "paint": "palette",
    "draw": "brush",
    "sculpt": "shape",
    "photo": "camera",
    "video": "video",
    "write": "pencil",
    "read": "book-open-page-variant",
    "code": "code-tags",    
    "sew": "needle",
    "cook": "chef-hat",
    "bake": "bread-slice",
    "dance": "dance-ballroom",
    "sing": "microphone-variant",
    "music": "music",
    "game": "gamepad-variant",
    "chess": "chess-king",
    "puzzle": "puzzle",
    "yoga": "yoga",
    "meditation": "meditation",
    "travel": "airplane",
    "shop": "cart",
    "collect": "package-variant",
    "model": "human-male",
    "woodwork": "axe",    
    "robot": "robot-industrial",    
    "journal": "book",
    "calligraphy": "pen",
    "pottery": "pot-mix",
    "surf": "surfing",
    "ski": "ski",
    "snowboard": "snowboard",
    "kitesurfing": "kitesurfing",
    "skate": "skateboard",
    "study": "school",
    "box": "boxing-glove",
    "martial": "karate",
    "archery": "bow-arrow",
    "horse": "horse-human",      
    "design": "vector-point-edit",
    "tattoo": "needle",
    "brew": "beer",    
    "cosplay": "face-man-shimmer",
    "magic": "cards",
    "film": "filmstrip",
    "act": "theater",
    "tree": "pine-tree",
    "dog": "dog",
    "cat": "cat",
    "gymnastics": "gymnastics",
    "workout": "dumbbell",
    "craft": "hammer-wrench",
    "sleep": "sleep",    
}

model = None
key_embeddings = None
keys = list(canonical_icon_map.keys())

def load_model():
    from sentence_transformers import SentenceTransformer
    global model, key_embeddings    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    key_embeddings = model.encode(keys, convert_to_tensor=True)

def is_model_loaded():
    return model is not None and key_embeddings is not None

def match_user_input(user_input):
    from sentence_transformers import util
    if not is_model_loaded():
        print("Model not loaded yet. Please wait.")
        return None
    input_embedding = model.encode(user_input, convert_to_tensor=True)
    scores = util.cos_sim(input_embedding, key_embeddings)[0]
    best_match_idx = scores.argmax().item()
    best_key = keys[best_match_idx]
    return canonical_icon_map[best_key]