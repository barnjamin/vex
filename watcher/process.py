import os

base_path = "/tmp/boxtmp"

def get_app_path(app_id: int):
    return f"{base_path}/{app_id}"

def get_box_path(app_id: int, box_name: str):
    return f"{get_app_path(app_id)}/{box_name}" 

def process_app(app_id: int):
    box_names = os.listdir(get_app_path(app_id))
    for box_name in box_names:
        process_boxes(app_id, box_name)

def process_boxes(app_id: int, box_name: str):
    box_raw_name = bytes.fromhex(box_name)
    print(box_raw_name.decode())

    box_path = get_box_path(app_id, box_name)
    box_rounds = os.listdir(box_path)
    # make sure we process them in order
    rounds = sorted([int(round) for round in box_rounds])

    for round in rounds: 
        box_round_path = f"{box_path}/{round}"
        #print("Working on round: ", round)
        #with open(box_round_path, 'rb') as f:
        #    box_contents = f.read()
        #    print(len(box_contents))



if __name__ == "__main__":
    app_id = 612
    process_app(app_id)