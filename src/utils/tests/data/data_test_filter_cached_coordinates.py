parameters_filter_cached_coordinates_empty_cached_tiles_dir = \
    [([(512, 768), (768, 768), (512, 1024), (768, 1024)],
      [(512, 768), (768, 768), (512, 1024), (768, 1024)]),
     ([(512, -768), (768, -768), (512, -512), (768, -512)],
      [(512, -768), (768, -768), (512, -512), (768, -512)]),
     ([(-1024, -768), (-768, -768), (-1024, -512), (-768, -512)],
      [(-1024, -768), (-768, -768), (-1024, -512), (-768, -512)]),
     ([(-1024, 768), (-768, 768), (-1024, 1024), (-768, 1024)],
      [(-1024, 768), (-768, 768), (-1024, 1024), (-768, 1024)]),
     ([(-256, 0), (0, 0), (-256, 256), (0, 256)],
      [(-256, 0), (0, 0), (-256, 256), (0, 256)])]

parameters_filter_cached_coordinates_not_empty_cached_tiles_dir = \
    [([(512, 768), (768, 768), (512, 1024), (768, 1024)],
      [(512, 768), (768, 768)]),
     ([(512, -768), (768, -768), (512, -512), (768, -512)],
      [(512, -768), (768, -768)]),
     ([(-1024, -768), (-768, -768), (-1024, -512), (-768, -512)],
      [(-1024, -768), (-768, -768)]),
     ([(-1024, 768), (-768, 768), (-1024, 1024), (-768, 1024)],
      [(-1024, 768), (-768, 768)]),
     ([(-256, 0), (0, 0), (-256, 256), (0, 256)],
      [(-256, 0), (0, 0)]),

     ([(512, 1024), (768, 1024)],
      []),
     ([(512, -512), (768, -512)],
      []),
     ([(-1024, -512), (-768, -512)],
      []),
     ([(-1024, 1024), (-768, 1024)],
      []),
     ([(-256, 256), (0, 256)],
      [])]
