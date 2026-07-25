import math
import random
from panda3d.core import Filename, Fog, LColor
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

Texture.default_filtering = False
app = Ursina()

# i was going to put fog but it ends up covering the entire Skybox and making the sky white, flashbanging you

window.title = "EmerEng (RD)"
window.borderless = False
window.fps_counter.enabled = False
window.exit_button.visible = False

# Change the path So the atlas doesn't make the textures white, or Lilac Squares if the UV's arent positioned correctly
tex_path = Filename.fromOsSpecific(r'C:\Users\(user)\(project's Folder)\PythonProject\(assets folder)\file.png')
raw_tex = loader.loadTexture(tex_path)
atlas_texture = Texture(raw_tex)

block_pick = 1

crosshair_h = Entity(parent=camera.ui, model='quad', color=color.light_gray, scale=(0.02, 0.003))
crosshair_v = Entity(parent=camera.ui, model='quad', color=color.light_gray, scale=(0.003, 0.02))

CHUNK_SIZE = 16
CHUNK_ENTITIES = {}
WORLD_DATA = {}


def fade(t): return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(t, a, b): return a + t * (b - a) #lerp


def grad(hash, x, y):
    h = hash & 7
    u = x if h < 4 else y
    v = y if h < 4 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -2 * v)


_P_BASE = [151, 160, 137, 91, 90, 15, 131, 13, 201, 95, 96, 53, 194, 233, 7, 225, 140, 36, 103, 30, 69, 142, 8, 99, 37,
           240, 21, 10,
           23, 190, 6, 148, 247, 120, 234, 75, 0, 26, 197, 62, 94, 252, 219, 203, 117, 35, 11, 32, 57, 177, 33, 88, 237,
           149,
           56, 87, 174, 20, 125, 136, 171, 168, 68, 175, 74, 165, 71, 134, 139, 48, 27, 166, 77, 146, 158, 231, 83, 111,
           229,
           122, 60, 211, 133, 230, 220, 105, 92, 41, 55, 46, 245, 40, 244, 102, 143, 54, 65, 25, 63, 161, 1, 216, 80,
           73,
           209, 76, 132, 187, 208, 89, 18, 169, 200, 196, 135, 130, 116, 188, 159, 86, 164, 100, 109, 198, 173, 186, 3,
           64, 52, 217, 226, 250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85, 212, 207, 206, 59, 227, 47, 16, 58,
           17,
           182, 189, 28, 42, 223, 183, 170, 213, 119, 248, 152, 2, 44, 154, 163, 70, 221, 153, 101, 155, 167, 43, 172,
           9,
           129, 22, 39, 253, 19, 98, 108, 110, 79, 113, 224, 232, 178, 185, 112, 104, 218, 246, 97, 228, 251, 34, 242,
           193,
           238, 210, 144, 12, 191, 179, 162, 241, 81, 51, 145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106,
           157, 184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205, 93, 222, 114, 67, 29, 24, 72, 243,
           141, 128, 195, 78, 66, 215, 61, 156, 180]
P = _P_BASE * 2


def noise2d(x, y):
    X = math.floor(x) & 255
    Y = math.floor(y) & 255
    x -= math.floor(x)
    y -= math.floor(y)
    u = fade(x)
    v = fade(y)
    A = P[X] + Y
    B = P[X + 1] + Y
    return lerp(v, lerp(u, grad(P[A], x, y), grad(P[B], x - 1, y)),
                lerp(u, grad(P[A + 1], x, y - 1), grad(P[B + 1], x - 1, y - 1)))


def get_block(wx, wy, wz):
    if (wx, wy, wz) in WORLD_DATA:
        return WORLD_DATA[(wx, wy, wz)]

    if wy < 0: return 2

    hills = noise2d(wx * 0.015, wz * 0.015) * 8
    detail = noise2d(wx * 0.08, wz * 0.08) * 2
    surface_height = int(5 + hills + detail)

    if wy < surface_height:
        b_type = 2
    elif wy == surface_height:
        b_type = 1
    else:
        b_type = 0

    WORLD_DATA[(wx, wy, wz)] = b_type
    return b_type

#This will be removed/moved later for clearer experience
def generate_chunk_mesh(cx, cz):
    verts = []
    tris = []
    uvs = []
    vertex_count = 0

    faces = {
        'top': {'v': [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], 't': [0, 1, 2, 0, 2, 3]},
        'bottom': {'v': [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)], 't': [0, 1, 2, 0, 2, 3]},
        'left': {'v': [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], 't': [0, 2, 1, 0, 3, 2]},
        'right': {'v': [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)], 't': [0, 2, 1, 0, 3, 2]},
        'front': {'v': [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 't': [0, 2, 1, 0, 3, 2]},
        'back': {'v': [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)], 't': [0, 2, 1, 0, 3, 2]},
    }

    tile_size = 1.0 / 16.0
    v_offset_val = 1.0 - tile_size
    eps = 0.0001

    grass_all = [
        (0.0 + eps, v_offset_val + eps),
        (0.0 + tile_size - eps, v_offset_val + eps),
        (0.0 + tile_size - eps, v_offset_val + tile_size - eps),
        (0.0 + eps, v_offset_val + tile_size - eps)
    ]

    cobble_all = [
        (tile_size + eps, v_offset_val + eps),
        (tile_size * 2 - eps, v_offset_val + eps),
        (tile_size * 2 - eps, v_offset_val + tile_size - eps),
        (tile_size + eps, v_offset_val + tile_size - eps)
    ]

    water_all = [
        (tile_size * 2 + eps, v_offset_val + eps),
        (tile_size * 3 - eps, v_offset_val + eps),
        (tile_size * 3 - eps, v_offset_val + tile_size - eps),
        (tile_size * 2 + eps, v_offset_val + tile_size - eps)
    ]

    wood_all = [
        (tile_size * 5 + eps, v_offset_val + eps),
        (tile_size * 6 - eps, v_offset_val + eps),
        (tile_size * 6 - eps, v_offset_val + tile_size - eps),
        (tile_size * 5 + eps, v_offset_val + tile_size - eps)
    ]

    leaves_all = [
        (tile_size * 5 + eps, v_offset_val + eps),
        (tile_size * 6 - eps, v_offset_val + eps),
        (tile_size * 6 - eps, v_offset_val + tile_size - eps),
        (tile_size * 5 + eps, v_offset_val + tile_size - eps)
    ]

    for lx in range(CHUNK_SIZE):
        for lz in range(CHUNK_SIZE):
            for wy in range(16):
                wx = cx * CHUNK_SIZE + lx
                wz = cz * CHUNK_SIZE + lz

                block_id = get_block(wx, wy, wz)
                if block_id == 0:
                    continue

                check_directions = {
                    'top': get_block(wx, wy + 1, wz) == 0,
                    'bottom': get_block(wx, wy - 1, wz) == 0,
                    'left': get_block(wx - 1, wy, wz) == 0,
                    'right': get_block(wx + 1, wy, wz) == 0,
                    'front': get_block(wx, wy, wz + 1) == 0,
                    'back': get_block(wx, wy, wz - 1) == 0,
                }

                for face_name, should_render in check_directions.items():
                    if should_render:
                        face = faces[face_name]

                        for v_vert in face['v']:
                            vx, vy, vz = v_vert[0], v_vert[1], v_vert[2]

                            if block_id == 4 and vy == 1:
                                vy = 0.4 
                            verts.append((lx + vx, wy + vy, lz + vz))

                        if block_id == 1:
                            uvs.extend(grass_all)
                        elif block_id == 2:
                            uvs.extend(cobble_all)
                        elif block_id == 3:
                            uvs.extend(water_all)
                        elif block_id == 4:
                            uvs.extend(wood_all)  # wud
                        elif block_id == 5:
                            uvs.extend(leaves_all)  # left
                        else:
                            uvs.extend(grass_all) 
                        for t in face['t']:
                            tris.append(vertex_count + t)
                        vertex_count += 4

    if not verts:
        return None
    return Mesh(vertices=verts, triangles=tris, uvs=uvs, mode='triangle')


def load_chunk(cx, cz):
    if (cx, cz) in CHUNK_ENTITIES:
        return
    mesh = generate_chunk_mesh(cx, cz)
    if mesh:
        ent = Entity(
            model=mesh,
            texture=atlas_texture,
            position=(cx * CHUNK_SIZE, 0, cz * CHUNK_SIZE),
            collider='mesh',
        )
        CHUNK_ENTITIES[(cx, cz)] = ent
    else:
        CHUNK_ENTITIES[(cx, cz)] = 'empty'


def reload_chunk(cx, cz):
    if (cx, cz) in CHUNK_ENTITIES and CHUNK_ENTITIES[(cx, cz)] != 'empty':
        destroy(CHUNK_ENTITIES[(cx, cz)])
        del CHUNK_ENTITIES[(cx, cz)]
    elif (cx, cz) in CHUNK_ENTITIES:
        del CHUNK_ENTITIES[(cx, cz)]
    load_chunk(cx, cz)

class BlockParticle(Entity):
    def __init__(self, position, floor_y, block_id=1):
        u_uv = 0.0
        if block_id == 2:
            u_uv = 1.0 / 16.0       # cobble :)
        elif block_id in (3, 4): # (OLD) Water n Wood
            u_uv = 2.0 / 16.0      # lilac water texture heheh
        else:
            u_uv = 0.0           

        super().__init__(
            model='quad',
            texture=atlas_texture,
            texture_scale=(1/16, 1/16),
            texture_offset=(u_uv, 15/16),
            position=position + Vec3(random.uniform(0.2, 0.8), random.uniform(0.3, 0.7), random.uniform(0.2, 0.8)),
            scale=random.uniform(0.08, 0.12),
            double_sided=True,
            unlit=True,
            billboard=True  
        )
        self.velocity = Vec3(random.uniform(-1.5, 1.5), random.uniform(2.5, 4.0), random.uniform(-1.5, 1.5))
        self.gravity = 14.0
        self.floor_y = floor_y
        self.is_grounded = False
        self.ground_timer = 1.0

    def update(self):
        if self.is_grounded:
            self.ground_timer -= time.dt
            if self.ground_timer <= 0:
                destroy(self)
            return

        self.velocity.y -= self.gravity * time.dt
        self.position += self.velocity * time.dt

        if self.y <= self.floor_y:
            self.y = self.floor_y
            self.velocity = Vec3(0, 0, 0)
            self.is_grounded = True

#Will be grouped later.
def spawn_tree_at(base_x, base_y, base_z):
    affected_chunks = set()

    trunk_height = 4
    for h in range(trunk_height):
        ty = base_y + h
        WORLD_DATA[(base_x, ty, base_z)] = 4
        affected_chunks.add((math.floor(base_x / CHUNK_SIZE), math.floor(base_z / CHUNK_SIZE)))

    canopy_start_y = base_y + trunk_height - 1
    for dx in range(-1, 2):
        for dz in range(-1, 2): 
            for dy in range(2): 
                lx = base_x + dx
                ly = canopy_start_y + dy
                lz = base_z + dz

                if get_block(lx, ly, lz) == 0:
                    WORLD_DATA[(lx, ly, lz)] = 6
                    affected_chunks.add((math.floor(lx / CHUNK_SIZE), math.floor(lz / CHUNK_SIZE)))

    for cx, cz in affected_chunks:
        reload_chunk(cx, cz)

def spawn_break_particles(bx, by, bz, block_id):
    floor_level = float(by)
    for _ in range(16):
        BlockParticle(Vec3(bx, by, bz), floor_y=floor_level, block_id=block_id)

def input(key): #This handles player Inputs, Dev Note: Interaction logic depends on Mouse Raycasting
    (mouse.hovered_entity) and requires chunk colliders to be loaded.
    global block_pick

    if key == 'r':
        # It only teleports you to the only chunks you have loaded in
        random_x = random.randint(-16, 32)
        random_z = random.randint(-16, 32)
# This line teleports you directly on top of the land, and confirms that you wont collide with cobblestone or grass and accidentally fall thru the void
        surface_y = get_block(random_x, 10, random_z) 
        

        # tp
        player.x = random_x
        player.z = random_z
        player.y = 15
        return  

    if key == 't':
        if mouse.hovered_entity:
            target_pos = mouse.point + mouse.normal * 0.5
            bx = math.floor(target_pos.x)
            by = math.floor(target_pos.y)
            bz = math.floor(target_pos.z)

            spawn_tree_at(bx, by, bz)
        return

    if key == 'left mouse down' or key == 'right mouse down':
        if mouse.hovered_entity:
            if key == 'left mouse down':
                target_pos = mouse.point - mouse.normal * 0.001
            else:
                target_pos = mouse.point + mouse.normal * 0.5

            bx = math.floor(target_pos.x)
            by = math.floor(target_pos.y)
            bz = math.floor(target_pos.z)

            if key == 'left mouse down':
                b_id = get_block(bx, by, bz)
                WORLD_DATA[(bx, by, bz)] = 0
                spawn_break_particles(bx, by, bz, b_id)
            else:
                WORLD_DATA[(bx, by, bz)] = block_pick
                
            cx = math.floor(bx / CHUNK_SIZE)
            cz = math.floor(bz / CHUNK_SIZE)

            reload_chunk(cx, cz)

            if bx % CHUNK_SIZE == 0: reload_chunk(cx - 1, cz)
            if bx % CHUNK_SIZE == CHUNK_SIZE - 1: reload_chunk(cx + 1, cz)
            if bz % CHUNK_SIZE == 0: reload_chunk(cx, cz - 1)
            if bz % CHUNK_SIZE == CHUNK_SIZE - 1: reload_chunk(cx, cz + 1)


for x_offset in range(-1, 2):
    for z_offset in range(-1, 2):
        load_chunk(x_offset, z_offset)

sky = Sky()
sky.color = color.rgb(135, 206, 235)

player = FirstPersonController()
player.x = 8
player.z = 8
player.y = 14
player.jump_height = 1.4

walk_speed = 5
sprint_speed = 8

water_timer = 0.0
water_tick_rate = 0.2


water_tick_rate = 0.2
# Cellular automata water simulation, this will be moved later in v0.7-v0.9
def process_water_flow():
    current_water_blocks = [pos for pos, b_type in list(WORLD_DATA.items()) if b_type == 3]
    chunks_to_reload = set()

    for (bx, by, bz) in current_water_blocks:
        if WORLD_DATA.get((bx, by - 1, bz), 0) == 0:
            WORLD_DATA[(bx, by - 1, bz)] = 3
            chunks_to_reload.add((math.floor(bx / CHUNK_SIZE), math.floor(bz / CHUNK_SIZE)))
            continue

        neighbors = [(bx - 1, by, bz), (bx + 1, by, bz), (bx, by, bz - 1), (bx, by, bz + 1)]
        for nx, ny, nz in neighbors:
            if WORLD_DATA.get((nx, ny, nz), 0) == 0:
                if ny <= 6:
                    WORLD_DATA[(nx, ny, nz)] = 3
                    chunks_to_reload.add((math.floor(nx / CHUNK_SIZE), math.floor(nz / CHUNK_SIZE)))

    for cx, cz in chunks_to_reload:
        reload_chunk(cx, cz)


def update():
    global block_pick, water_timer 

    if held_keys['1']: block_pick = 1
    if held_keys['2']: block_pick = 2
    if held_keys['3']: block_pick = 3
    if held_keys['4']: block_pick = 4 
    if held_keys['escape']: quit()

    water_timer += time.dt
    if water_timer >= water_tick_rate:
        process_water_flow()
        water_timer = 0.0 

    if held_keys['left shift']:
        player.speed = sprint_speed
    else:
        player.speed = walk_speed

    p_cx = math.floor(player.x / CHUNK_SIZE)
    p_cz = math.floor(player.z / CHUNK_SIZE)
    for xo in range(-1, 2):
        for zo in range(-1, 2):
            load_chunk(p_cx + xo, p_cz + zo)


app.run()
