from .models import Block


def read_road(road):
    road_map = list(road.get_ancestors(include_self=True))
    print(road_map)
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
