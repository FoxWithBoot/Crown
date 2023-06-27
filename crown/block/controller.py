from .models import Block


def read_road(road):
    road_map = list(road.get_ancestors(include_self=True))
    start_block = None
    for i in road_map[::-1]:
        start_block = Block.objects.filter(road=i, is_start=True)
        if start_block.exists():
            start_block = start_block[0]
            break
    qs = []
    _get_blocks_of_the_road(block=start_block,
                            road_map=road_map,
                            road_map_i=road_map.index(start_block.road),
                            qs=qs)
    return qs


def _get_blocks_of_the_road(block, road_map, road_map_i, qs):
    qs.append(block)
    block_n = block
    if block.next_blocks.count() == 0:
        """Если конец дороги, то отдать путь"""
        return qs
    if block.next_blocks.count() > 0:
        """Если развилка"""
        is_next_road_exists = False
        i = road_map_i
        while i < len(road_map):
            """Проходит по всем слудующим дорогам в маршруте"""
            i += 1
            if len(road_map) > i and block.next_blocks.filter(road=road_map[i]).exists():
                """Если есть блок с целевой (следующей) дороги, то добавить его"""
                block_n = block.next_blocks.get(road=road_map[i])
                is_next_road_exists = True
                road_map_i = i
                break

        if is_next_road_exists:
            pass
        elif block.next_blocks.filter(road=block.road).exists():
            """Если есть блок с той же дороги, то добавить его"""
            block_n = block.next_blocks.get(road=block.road)
        else:
            """Иначе перейти на главную дорогу"""
            road_map_i -= 1
            while not block.next_blocks.filter(road=road_map[road_map_i]).exists():
                if road_map_i < 0:
                    """Если среди предыдущих блоков нет блока с дороги-предка, то отдать путь"""
                    return qs
                road_map_i -= 1
            block_n = block.next_blocks.get(road=road_map[road_map_i])
    _get_blocks_of_the_road(block_n, road_map, road_map_i, qs)


def create_block(road, line, content, where):
    new_block = Block.objects.create(road=road, content=content)
    print(f"Создан блок {new_block} на дороге {road.id}")

    index = line.index(where['block'])
    if where['before_after'] == 'after':
        index += 1

    line.insert(index, new_block)
    pre_block, next_block = _get_neighbours(line, new_block)

    if pre_block and next_block:
        pre_block.next_blocks.add(new_block)
        print(f"Добавлена связь {pre_block} -> {new_block}")
        new_block.next_blocks.add(next_block)
        print(f"Добавлена связь {new_block} -> {next_block}")
        if pre_block.road != road and next_block.road != road:
            pass
        else:
            pre_block.next_blocks.remove(next_block)
            print(f"Удалена связь {pre_block} -> {next_block}")
    if not pre_block:
        new_block.is_start = True
        new_block.save()
        if next_block.road == road:
            next_block.is_start = False
            next_block.save()
            print(f"Для блока {next_block} is_start установлено в False")
        new_block.next_blocks.add(next_block)
        print(f"Добавлена связь {new_block} -> {next_block}")
    if not next_block:
        pre_block.next_blocks.add(new_block)
        print(f"Добавлена связь {pre_block} -> {new_block}")
    return new_block


def _get_neighbours(line, block):
    pre_block = None
    next_block = None
    index = line.index(block)
    if index > 0:
        pre_block = line[index - 1]
    if index < len(line) - 1:
        next_block = line[index + 1]
    return pre_block, next_block


def update_block_content(block, road, line, content):
    pre_block, next_block = _get_neighbours(line, block)
    block_cr = Block.objects.create(road=road, content=content)
    if pre_block and next_block:  # Есть и пред и след блоки
        pre_block.next_blocks.add(block_cr)
        print(f"Добавлена связь {pre_block} -> {block_cr}")
        block_cr.next_blocks.add(next_block)
        print(f"Добавлена связь {block_cr} -> {next_block}")
        if pre_block.road != road and next_block.road != road:  # Если и предыдущий и следующий не с моей дороги
            pass
        else:
            if pre_block.road == road:  # Если пред блок с моей дороги
                pre_block.next_blocks.remove(block)
                print(f"Удалена связь {pre_block} -> {block}")
            if next_block.road == road:  # Если след блок с моей дороги
                block.next_blocks.remove(next_block)
                print(f"Удалена связь {block} -> {next_block}")
    elif not pre_block:  # Нет пред блока
        block_cr.is_start = True
        block_cr.save()
        print(f"Для блока {block_cr} is_start установлено в True")
        block_cr.next_blocks.add(next_block)
        print(f"Добавлена связь {block_cr} -> {next_block}")
        if next_block.road == road:  # След блок с моей дороги
            block.next_block.remove(next_block)
            print(f"Удалена связь {block} -> {next_block}")
    elif not next_block:  # Конец линии
        pre_block.next_blocks.add(block_cr)
        print(f"Добавлена связь {pre_block} -> {block_cr}")
        if pre_block.road == road:  # Если пред блок с моей дороги
            pre_block.next_blocks.remove(block)
            print(f"Удалена связь {pre_block} -> {block}")

    _create_connect_with_new_block(block_cr, block, road)

    return block_cr


def _create_connect_with_new_block(new_block, old_block, road):
    list_of_pre_blocks = list(Block.objects.filter(next_blocks__in=[old_block]))
    list_of_next_blocks = list(old_block.next_blocks.all())

    for b in list_of_next_blocks:
        #if _check_paternity(road, b.road):
        if b.road in road.get_descendants():
            old_block.next_blocks.remove(b)
            #logging.info(f"Удалена связь {old_block} -> {b}")
            print(f"Удалена связь {old_block} -> {b}")
            new_block.next_blocks.add(b)
            #logging.info(f"Добавлена связь {new_block} -> {b}")
            print(f"Добавлена связь {new_block} -> {b}")

    for b in list_of_pre_blocks:
        if b.road in road.get_descendants():
            b.next_blocks.remove(old_block)
            #logging.info(f"Удалена связь {b} -> {old_block}")
            print(f"Удалена связь {b} -> {old_block}")
            b.next_blocks.add(new_block)
            #logging.info(f"Добавлена связь {b} -> {new_block}")
            print(f"Добавлена связь {b} -> {new_block}")
