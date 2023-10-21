from django.db.models import Q

from .models import Block, BlocksOnRoad
from road.models import Road


def read_road(road):
    blocks_list = BlocksOnRoad.objects.filter(road=road).order_by('index').values_list('block', flat=True)
    blocks = []
    for i in blocks_list:
        blocks.append(Block.objects.get(pk=i))
    return blocks

# def read_road(road):
#     road_map = list(road.get_ancestors(include_self=True))
#     start_block = None
#     for i in road_map[::-1]:
#         start_block = Block.objects.filter(road=i, is_start=True)
#         if start_block.exists():
#             start_block = start_block[0]
#             break
#     qs = []
#     _get_blocks_of_the_road(block=start_block,
#                             road_map=road_map,
#                             road_map_i=road_map.index(start_block.road),
#                             qs=qs)
#     return qs
#
#
# def _get_blocks_of_the_road(block, road_map, road_map_i, qs):
#     qs.append(block)
#     block_n = block
#     if block.next_blocks.count() == 0:
#         """Если конец дороги, то отдать путь"""
#         return qs
#     if block.next_blocks.count() > 0:
#         """Если развилка"""
#         is_next_road_exists = False
#         i = len(road_map)
#         while i >= road_map_i:
#             """Проходит по всем следующим дорогам в маршруте"""
#             i -= 1
#             r_i = road_map[i]
#             next_block = block.next_blocks.filter(road=r_i)
#             if len(road_map) > i and len(next_block) > 0:
#                 """Если есть блок с целевой (следующей) дороги, то добавить его"""
#                 block_n = next_block[0]
#                 is_next_road_exists = True
#                 road_map_i = i
#                 break
#
#         if is_next_road_exists:
#             pass
#         elif block.next_blocks.filter(road=block.road).exists():
#             """Если есть блок с той же дороги, то добавить его"""
#             block_n = block.next_blocks.get(road=block.road)
#         else:
#             """Иначе перейти на главную дорогу"""
#             road_map_i -= 1
#             while not block.next_blocks.filter(road=road_map[road_map_i]).exists():
#                 if road_map_i < 0:
#                     """Если среди предыдущих блоков нет блока с дороги-предка, то отдать путь"""
#                     return qs
#                 road_map_i -= 1
#             block_n = block.next_blocks.get(road=road_map[road_map_i])
#     _get_blocks_of_the_road(block_n, road_map, road_map_i, qs)


def create_block(road, content, where):
    index = BlocksOnRoad.objects.get(block=where['block'], road=road).index
    if where['before_after'] == 'after':
        index += 1
    new_block = Block.objects.create(content=content)
    new_block.insert_block(road, index)
    BlocksOnRoad.objects.create(road=road, block=new_block, index=index, original_road=True)

    orig_line = read_road(road)
    pre_block = orig_line[index-1] if index > 0 else None
    next_block = orig_line[index+1] if index < len(orig_line)-1 else None
    desc = road.get_descendants()

    for d in desc:
        tf = False
        line = read_road(d)
        if not pre_block and next_block in line and line.index(next_block) == 0:
            index = 0
            tf = True
        if not next_block and pre_block in line and line.index(pre_block) == len(line)-1:
            index = len(line)-1
            tf = True
        if pre_block and next_block and pre_block in line and next_block in line and \
                line.index(next_block)-line.index(pre_block) == 1:
            index = line.index(pre_block)
            tf = True
        if tf:
            new_block.insert_block(road=d, index=index)
            BlocksOnRoad.objects.create(road=d, block=new_block, index=index)

    return new_block


# def create_block(road, line, content, where):
#     new_block = Block.objects.create(road=road, content=content)
#     print(f"Создан блок {new_block} на дороге {road.id}")
#
#     index = line.index(where['block'])
#     if where['before_after'] == 'after':
#         index += 1
#
#     line.insert(index, new_block)
#     pre_block, next_block = _get_neighbours(line, new_block)
#
#     if pre_block and next_block:
#         pre_block.next_blocks.add(new_block)
#         print(f"Добавлена связь {pre_block} -> {new_block}")
#         new_block.next_blocks.add(next_block)
#         print(f"Добавлена связь {new_block} -> {next_block}")
#         if pre_block.road != road and next_block.road != road:
#             pass
#         else:
#             pre_block.next_blocks.remove(next_block)
#             print(f"Удалена связь {pre_block} -> {next_block}")
#     if not pre_block:
#         new_block.is_start = True
#         new_block.save()
#         if next_block.road == road:
#             next_block.is_start = False
#             next_block.save()
#             print(f"Для блока {next_block} is_start установлено в False")
#         new_block.next_blocks.add(next_block)
#         print(f"Добавлена связь {new_block} -> {next_block}")
#     if not next_block:
#         pre_block.next_blocks.add(new_block)
#         print(f"Добавлена связь {pre_block} -> {new_block}")
#     return new_block
#
#
# def _get_neighbours(line, block):
#     pre_block = None
#     next_block = None
#     index = line.index(block)
#     if index > 0:
#         pre_block = line[index - 1]
#     if index < len(line) - 1:
#         next_block = line[index + 1]
#     return pre_block, next_block

def update_block(block, road, content):
    connect = BlocksOnRoad.objects.get(road=road, block=block)
    if connect.original_road:
        block.content = content
        block.save()
        return block
    new_block = Block.objects.create(content=content)
    BlocksOnRoad.objects.create(road=road, block=new_block, original_road=True, index=connect.index)
    connect.delete()
    return new_block


# def update_block_content(block, road, line, content):
#     pre_block, next_block = _get_neighbours(line, block)
#     block_cr = Block.objects.create(road=road, content=content)
#     if pre_block and next_block:  # Есть и пред и след блоки
#         pre_block.next_blocks.add(block_cr)
#         print(f"Добавлена связь {pre_block} -> {block_cr}")
#         block_cr.next_blocks.add(next_block)
#         print(f"Добавлена связь {block_cr} -> {next_block}")
#         if pre_block.road != road and next_block.road != road:  # Если и предыдущий и следующий не с моей дороги
#             pass
#         else:
#             if pre_block.road == road:  # Если пред блок с моей дороги
#                 pre_block.next_blocks.remove(block)
#                 print(f"Удалена связь {pre_block} -> {block}")
#             if next_block.road == road:  # Если след блок с моей дороги
#                 block.next_blocks.remove(next_block)
#                 print(f"Удалена связь {block} -> {next_block}")
#     elif not pre_block:  # Нет пред блока
#         block_cr.is_start = True
#         block_cr.save()
#         print(f"Для блока {block_cr} is_start установлено в True")
#         block_cr.next_blocks.add(next_block)
#         print(f"Добавлена связь {block_cr} -> {next_block}")
#         if next_block.road == road:  # След блок с моей дороги
#             block.next_block.remove(next_block)
#             print(f"Удалена связь {block} -> {next_block}")
#     elif not next_block:  # Конец линии
#         pre_block.next_blocks.add(block_cr)
#         print(f"Добавлена связь {pre_block} -> {block_cr}")
#         if pre_block.road == road:  # Если пред блок с моей дороги
#             pre_block.next_blocks.remove(block)
#             print(f"Удалена связь {pre_block} -> {block}")
#
#     _create_connect_with_new_block(block_cr, block, road)
#
#     return block_cr
#
#
# def _create_connect_with_new_block(new_block, old_block, road):
#     list_of_pre_blocks = list(Block.objects.filter(next_blocks__in=[old_block]))
#     list_of_next_blocks = list(old_block.next_blocks.all())
#
#     for b in list_of_next_blocks:
#         if b.road in road.get_descendants():
#             old_block.next_blocks.remove(b)
#             #logging.info(f"Удалена связь {old_block} -> {b}")
#             print(f"Удалена связь {old_block} -> {b}")
#             new_block.next_blocks.add(b)
#             #logging.info(f"Добавлена связь {new_block} -> {b}")
#             print(f"Добавлена связь {new_block} -> {b}")
#
#     for b in list_of_pre_blocks:
#         if b.road in road.get_descendants():
#             b.next_blocks.remove(old_block)
#             #logging.info(f"Удалена связь {b} -> {old_block}")
#             print(f"Удалена связь {b} -> {old_block}")
#             b.next_blocks.add(new_block)
#             #logging.info(f"Добавлена связь {b} -> {new_block}")
#             print(f"Добавлена связь {b} -> {new_block}")

def delete_block(road, block):
    desc = road.get_descendants()
    connects = BlocksOnRoad.objects.filter(road__in=desc, block=block)
    for c in connects:
        c.block.cut_block(c.road)
    connects.delete()

    connect = BlocksOnRoad.objects.get(road=road, block=block)
    connect.block.cut_block(road)
    if connect.original_road:
        connect.block.delete()
    connect.delete()


# def delete_block(road, line, block):
#     list_roads_id_of_next_blocks = list(Block.objects.filter(next_blocks__in=[block]).values_list('road', flat=True))  # Список дорог, к которым относятся следующие блоки
#     list_roads_id_of_pre_blocks = list(block.next_blocks.all().values_list('road', flat=True))  # Список дорог, к которым относятся предыдущие блоки
#     roads_list = list(set(list_roads_id_of_next_blocks + list_roads_id_of_pre_blocks)) # Список дорог, к которым относятся связанные с удаляемым блоки
#
#     roads = []
#     for i in roads_list:
#         roads.append(Road.objects.get(pk=i))
#
#     print('Все дороги', roads)
#     if road in roads:
#         roads.remove(road)
#     print('Убрали целевую', roads)
#     r = roads.copy()
#     for i in roads:
#         #  Убрали кузенов
#         if i not in list(road.get_family()) and i in r:
#             r.remove(i)
#     roads = r.copy()
#     print('Убрали кузенов', roads)
#     # Удаляет из списка дорог предков целевой дороги
#     for i in roads:
#         if road in list(i.get_descendants()) and i in r:
#             r.remove(i)
#     roads = r.copy()
#     print('Убрали предков', roads)
#     for i in roads:
#         for j in roads:
#             if i != j:
#                 #  Убирает внуков целевой дороги
#                 if j in list(i.get_descendants()) and j in r:
#                     r.remove(j)
#     roads = r.copy()
#     print('Убрали внуков', roads)
#
#     for r_i in roads:
#         r_line = read_road(r_i)
#         pre_block, next_block = _get_neighbours(r_line, block)
#         pre_block, next_block = _pre_n_next_blocks_move(r_i, r_line, pre_block, block, next_block)
#         _new_pre_n_new_next_blocks_move(r_i, pre_block, block, next_block)
#
#     pre_block, next_block = _get_neighbours(line, block)
#     pre_block, next_block = _pre_n_next_blocks_move(road, line, pre_block, block, next_block)
#     if block.road == road:
#         block.delete()
#     return [pre_block, next_block]
#
#
# def _pre_n_next_blocks_move(road, line, pre_block, block, next_block):
#     pre_block_cr = pre_block
#     next_block_cr = next_block
#     if block.road == road:  # Если блок, который перемещают с моей дороги
#         if pre_block and next_block:  # Если существуют предыдущий и следующий блоки
#             #_cut_pre_my_next(road, pre_block, block, next_block)
#             pre_block.next_blocks.remove(block)
#             print(f"Удалена связь {pre_block} -> {block}")
#             block.next_blocks.remove(next_block)
#             print(f"Удалена связь {block} -> {next_block}")
#             if pre_block.road != road and next_block.road != road:  # Если и предыдущий и следующий не с моей дороги
#                 if not Block.objects.filter(id=pre_block.id, next_blocks__in=[next_block]).exists():  # Если предыдущий и следующий блоки НЕ связаны, то есть между ними на родительских дорогах есть промежуточные блоки
#                     pre_block_cr, next_block_cr = _cut_not_my_pre_block_not_my_next(road, line, pre_block, next_block)
#             else:
#                 pre_block.next_blocks.add(next_block)
#                 print(f"Добавлена связь {pre_block} -> {next_block}")
#         elif not pre_block:  # Если нет предыдущего блока, то есть block - это начало
#             block.next_blocks.remove(next_block)
#             print(f"Удалена связь {block} -> {next_block}")
#             block.is_start = False
#             block.save()
#             print(f"Для блока {block} is_start установлено в False")
#             if next_block.road != road:  # Если следующий блок не с моей дороги
#                 next_block_cr = Block.objects.create(road=road, is_start=True, content=next_block.content)
#                 print(f"Блок {next_block} скопирован в блок {next_block_cr}")
#                 if line.index(next_block) < len(line) - 1:  # Если следующий блок не последний в линии повествования
#                     next_block_cr.next_blocks.add(line[line.index(next_block) + 1])
#                     print(f"Добавлена связь {next_block_cr} -> {line[line.index(next_block) + 1]}")
#             else:
#                 next_block.is_start = True
#                 next_block.save()
#                 print(f"Для блока {next_block} is_start установлено в True")
#         elif not next_block:  # Если нет следующего блока, то есть block - это конец
#             pre_block.next_blocks.remove(block)
#             print(f"Удалена связь {pre_block} -> {block}")
#     else:  # Блок, который перемещают НЕ с моей дороги
#         if pre_block and next_block:  # Если существуют предыдущий и следующий блоки
#             if pre_block.road != road and next_block.road != road:  # Если и предыдущий, и следующий НЕ с моей дороги
#                 pre_block_cr, next_block_cr = _cut_not_my_pre_block_not_my_next(road, line, pre_block, next_block)
#             else:  # Предыдущий или следующий блок с моей дороги
#                 pre_block.next_blocks.add(next_block)
#                 print(f"Добавлена связь {pre_block} -> {next_block}")
#                 if pre_block.road == road:  # Если предыдущий блок с моей дороги
#                     pre_block.next_blocks.remove(block)
#                     print(f"Удалена связь {pre_block} -> {block}")
#                 if next_block.road == road:  # Если следующий блок с моей дороги
#                     block.next_blocks.remove(next_block)
#                     print(f"Удалена связь {block} -> {next_block}")
#         elif not pre_block:  # Если нет предыдущего блока, то есть block - это начало
#             if next_block.road != road:  # Если следующий блок HE с моей дороги
#                 next_block_cr = Block.objects.create(road=road, is_start=True, content=next_block.content)
#                 print(f"Блок {next_block} скопирован в блок {next_block_cr}")
#                 if line.index(next_block) < len(line) - 1:  # Если следующий блок не последний в линии повествования
#                     next_block_cr.next_blocks.add(line[line.index(next_block) + 1])
#                     print(f"Добавлена связь {next_block_cr} -> {line[line.index(next_block) + 1]}")
#                     if line[line.index(next_block) + 1].road == road:  # Если следующий за слудующим с моей дороги
#                         next_block.next_blocks.remove(line[line.index(next_block) + 1])
#                         print(f"Удалена связь {next_block} -> {line[line.index(next_block) + 1]}")
#             else:  # следующий блок с моей дороги
#                 block.next_blocks.remove(next_block)
#                 print(f"Удалена связь {block} -> {next_block}")
#                 next_block.is_start = True
#                 next_block.save()
#                 print(f"Для блока {next_block} is_start установлено в True")
#         elif not next_block:
#             if pre_block.road != road:  # Если предыдущий блок не с моей дороги
#                 pre_block_cr = Block.objects.create(road=road, content=pre_block.content)
#                 print(f"Блок {pre_block} скопирован в блок {pre_block_cr}")
#                 if line.index(pre_block) == 0:  # Если пред. блок - начало линии
#                     pre_block_cr.is_start = True
#                     pre_block_cr.save()
#                     print(f"Для блока {pre_block_cr} is_start установлено в True")
#                 else:  # Если пред. блок - НЕ начало линии
#                     line[line.index(pre_block) - 1].next_blocks.add(pre_block_cr)
#                     print(f"Добавлена связь {line[line.index(pre_block) - 1]} -> {pre_block_cr}")
#                     if line[line.index(pre_block) - 1].road == road:  # Если пред-предыдущий блок с моей дороги
#                         line[line.index(pre_block) - 1].next_blocks.remove(pre_block)
#                         print(f"Удалена связь {line[line.index(pre_block) - 1]} -> {pre_block}")
#             else:  # предыдущий блок с моей дороги
#                 pre_block.next_blocks.remove(block)
#                 print(f"Удалена связь {pre_block} -> {block}")
#
#     if pre_block != pre_block_cr:
#         _create_connect_with_new_block(pre_block_cr, pre_block, road)
#     if next_block != next_block_cr:
#         _create_connect_with_new_block(next_block_cr, next_block, road)
#
#     return pre_block_cr, next_block_cr
#
#
# def _cut_not_my_pre_block_not_my_next(road, line, pre_block, next_block):
#     pre_block_cr = Block.objects.create(road=road, content=pre_block.content)
#     #logging.info(f"Блок {pre_block} скопирован в блок {pre_block_cr}")
#     print(f"Блок {pre_block} скопирован в блок {pre_block_cr}")
#     if line.index(pre_block) == 0:  # Если предыдущий блок - начало линии
#         pre_block_cr.is_start = True
#         pre_block_cr.save()
#         #logging.info(f"Для блока {pre_block_cr} is_start установлено в True")
#     else:  # Если предыдущий блок НЕ начало линии
#         line[line.index(pre_block) - 1].next_blocks.add(pre_block_cr)
#         #logging.info(f"Добавлена связь {line[line.index(pre_block) - 1]} -> {pre_block_cr}")
#         print(f"Добавлена связь {line[line.index(pre_block) - 1]} -> {pre_block_cr}")
#         if line[line.index(pre_block) - 1].road == road:  # Если пред-предыдущий блок с моей дороги
#             line[line.index(pre_block) - 1].next_blocks.remove(pre_block)
#             #logging.info(f"Удалена связь {line[line.index(pre_block) - 1]} -> {pre_block}")
#             print(f"Удалена связь {line[line.index(pre_block) - 1]} -> {pre_block}")
#     next_block_cr = Block.objects.create(road=road, content=next_block.content)
#     #logging.info(f"Блок {next_block} скопирован в блок {next_block_cr}")
#     print(f"Блок {next_block} скопирован в блок {next_block_cr}")
#     if line.index(next_block) < len(line) - 1:  # Если следующий блок не последний в линии повествования
#         next_block_cr.next_blocks.add(line[line.index(next_block) + 1])
#         #logging.info(f"Добавлена связь {next_block_cr} -> {line[line.index(next_block) + 1]}")
#         print(f"Добавлена связь {next_block_cr} -> {line[line.index(next_block) + 1]}")
#         if line[line.index(next_block) + 1].road == road:  # Если следующий за слeдующим с моей дороги
#             next_block.next_blocks.remove(line[line.index(next_block) + 1])
#             #logging.info(f"Удалена связь {next_block} -> {line[line.index(next_block) + 1]}")
#             print(f"Удалена связь {next_block} -> {line[line.index(next_block) + 1]}")
#     pre_block_cr.next_blocks.add(next_block_cr)
#     #logging.info(f"Добавлена связь {pre_block_cr} -> {next_block_cr}")
#     print(f"Добавлена связь {pre_block_cr} -> {next_block_cr}")
#     return pre_block_cr, next_block_cr
#
#
# def _new_pre_n_new_next_blocks_move(road, new_pre_block, block, new_next_block):
#     i_d = block.id
#     if block.road != road:  # Блок, который перемещают HE с моей дороги
#         block = Block.objects.create(road=road, content=block.content, is_start=block.is_start)
#         print(f"Блок {i_d} скопирован в блок {block}")
#         _create_connect_with_new_block(block, Block.objects.get(pk=i_d), road)
#
#     if block.road == road:  # Блок, который перемещают с моей дороги
#         if new_pre_block and new_next_block:  # Если сществуют и предыдущий и следующий блоки
#             new_pre_block.next_blocks.add(block)
#             print(f"Добавлена связь {new_pre_block} -> {block}")
#             block.next_blocks.add(new_next_block)
#             print(f"Добавлена связь {block} -> {new_next_block}")
#             if new_pre_block.road != road and new_next_block.road != road:  # Если и предыдущий и следующий не с моей дороги
#                 pass
#             else:
#                 new_pre_block.next_blocks.remove(new_next_block)
#                 print(f"Удалена связь {new_pre_block} -> {new_next_block}")
#         elif not new_pre_block:  # Если нет предыдущего блока (то есть block - это новое начало)
#             block.next_blocks.add(new_next_block)
#             print(f"Добавлена связь {block} -> {new_next_block}")
#             block.is_start = True
#             block.save()
#             print(f"Для блока {block} is_start установлено в True")
#             if new_next_block.road != road:  # Если след.блок не с моей дороги
#                 pass
#             else:
#                 new_next_block.is_start = False
#                 new_next_block.save()
#                 print(f"Для блока {new_next_block} is_start установлено в False")
#         elif not new_next_block:  # Если нет следующего блока (то есть block - это конец)
#             new_pre_block.next_blocks.add(block)
#             print(f"Добавлена связь {new_pre_block} -> {block}")
#     return block


# def merge_roads(road, m_road):
#     one_line = read_road(road)
#     two_line = read_road(m_road)
#     road_map = list(m_road.get_ancestors(include_self=True))
#     descendants = road.get_descendants()
#
#     for bl in one_line:
#         if not bl in two_line:
#             pre_block, next_block = _get_neighbours(one_line, bl)
#
#             list_roads_id_of_next_blocks = list(Block.objects.filter(next_blocks__in=[bl]).values_list('road', flat=True))
#             list_roads_id_of_pre_blocks = list(bl.next_blocks.all().values_list('road', flat=True))
#             roads_list = list(set(list_roads_id_of_next_blocks + list_roads_id_of_pre_blocks))
#
#             roads = []
#             for i in roads_list:
#                 roads.append(Road.objects.get(pk=i))
#
#             for r in road_map:
#                 if r in roads:
#                     roads.remove(r)
#             for i in roads:
#                 for j in roads:
#                     if i != j:
#                         if j in i.get_descendants():
#                             roads.remove(j)
#
#             if bl.road == road or bl.road in descendants:
#                 if pre_block:
#                     pre_block.next_blocks.remove(bl)
#                 if next_block:
#                     bl.next_blocks.remove(next_block)
#                 one_line[one_line.index(bl)] = None
#                 bl.delete()
#
#             for r in roads:
#                 r.delete()
#
#     for i in range(len(two_line)):
#         if two_line[i].road != road and two_line[i].road in descendants:
#             two_line[i].road = road
#             two_line[i].save()
#         if i > 0 and two_line[i].is_start:
#             two_line[i].is_start = False
#             two_line[i].save()
#
#     index = road_map.index(road)
#     for i in range(index+1, len(road_map)):
#         Road.objects.filter(parent=road_map[i]).update(parent=road)
#         # if road_map[i].author != road.author: #and \
#         #         #not Road.objects.filter(id=road.id, co_authors=road_map[i].author).exists():
#         #     road.co_authors.add(road_map['road_map'][i].author)
#         road_map[i].delete()

def merge_roads(road, m_road):
    anc = m_road.get_ancestors(ascending=True)
    print(anc)
    #  print(BlocksOnRoad.objects.filter(road=m_road).count())
    roads = []
    for r in anc:
        roads.append(r)
        if r == road:
            break
        # blocks = BlocksOnRoad.objects.filter(Q(road=r))
        # cc = BlocksOnRoad.objects.filter(road=r)
        # #bl_ids = cc.values_list('block__id', flat=True)
        # #Block.objects.filter(id__in=bl_ids).delete()
        # cc.delete()
        # if r == road:
        #     break
        # r.delete()
    # for r in anc:
    #     if r == road:
    #         break

    line_m = read_road(m_road)

    BlocksOnRoad.objects.filter(road__in=roads).delete()

    # print('line:', line_m)
    # # blocks = line_m
    # # for r in roads:
    # #     blocks += read_road(r)
    # # blocks = list(set(blocks))
    # # print('blocks:', blocks)
    # print(BlocksOnRoad.objects.filter(road=m_road).count())
    # connects = BlocksOnRoad.objects.filter(road__in=roads, original_road=True)
    # for c in connects:
    #     if c.block not in line_m:
    #         c.block.delete()
            # c.delete()

    # for b in blocks:
    #     # if b not in line_m:
    #     #     b.delete()
    #     tf = True
    #     for c in BlocksOnRoad.objects.filter(block=b):
    #         if c.road not in roads:
    #             tf = False
    #             break
    #     if not tf:
    #         b.delete()

    # for b in line_m:
    #     for r in roads:
    # connects = BlocksOnRoad.objects.filter(Q(road__in=roads) & ~Q(block__in=line_m))
    # for c in connects:
    #     c.block.delete()

    # blocks = BlocksOnRoad.objects.filter(Q(road__in=roads) & ~Q(block__in=read_road(m_road)))
    # blocks.delete()
    #

    print('m_road: ', BlocksOnRoad.objects.filter(road=m_road).count(), len(read_road(m_road)))
    print('road: ', BlocksOnRoad.objects.filter(road=road).count(), len(read_road(road)))
    #BlocksOnRoad.objects.filter(road=m_road, original_road=True).update(road=road, original_road=True)

    i = 0
    for b in line_m:
        BlocksOnRoad.objects.create(road=road, block=b, original_road=True, index=i)
        i += 1
        print('m_road: ', BlocksOnRoad.objects.filter(road=m_road).count(), len(read_road(m_road)))
    print('road: ', BlocksOnRoad.objects.filter(road=road).count(), len(read_road(road)))

    # for r in reversed(roads):BlocksOnRoad.objects.filter(Q(road__in=roads) & Q(original_road=True) & ~Q(block__in=line_m)).delete()

    # m_road.delete()# for r in list(reversed(roads))[1:]:#    r.delete()
    roads.remove(road)
    roads.append(m_road)
    connects = BlocksOnRoad.objects.filter(Q(road__in=roads) & ~Q(block__in=line_m) & Q(original_road=True))
    for c in connects:
        c.block.delete()

    print(roads, m_road, roads[1:])
    # road.get_descendants().filter(~Q(pk__in=[r.id for r in roads])).update(parent=road)
    for r in list(reversed(roads)):
        r.get_children().filter(~Q(pk__in=[r.pk for r in roads])).update(parent=road)
        r.delete()

    collect_rubbish(road.get_root())
    recur(road)
    print('RUBBISH ROAD 2')

    roads = road.get_root().get_descendants(include_self=True)
    for r in roads:
        connects = BlocksOnRoad.objects.filter(road=r).order_by('index')
        i = 0
        for c in connects:
            if c.index != i:
                c.index = i
                c.save()
            i += 1


def collect_rubbish(road):
    print('RUBBISH')
    for b in Block.objects.all():
        con = BlocksOnRoad.objects.filter(block=b, original_road=True)
        if not con.exists():
            b.delete()
    print('RUBBISH BLOCK')
    for r in list(road.get_descendants())[::-1]:
        con = BlocksOnRoad.objects.filter(road=r)
        if not con.exists():
            print(r)
            r.delete()

    print('RUBBISH ROAD')


def recur(road):
    if road.is_leaf_node():
        return
    for r in road.get_children():
        line_road = read_road(road)
        line_r = read_road(r)
        arr = list(set(line_road) & set(line_r))
        if road.id == 1 and r.id == 3:
            print(line_road, line_r, arr)
        if len(arr) == 0:
            print(r)
            r.delete()
        else:
            recur(r)

