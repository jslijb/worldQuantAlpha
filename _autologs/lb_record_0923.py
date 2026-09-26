# -*- coding: utf-8 -*-
"""一次性：把 0924 13:36 截图（=0923 3AM EST 刷新榜）转录进 top30 日档"""
import sys
sys.path.insert(0, r'D:\Python\worldquant\_autologs')
from lb_record import record

rows = [
    (1,'YX42680',0.84,34,13077,0.53,''),
    (2,'CS35156',0.84,38,17312,0.65,'Chongqing University of Posts and Telecommunications'),
    (3,'FL70603',0.80,46,13616,0.82,'Peking University'),
    (4,'Ke Wang',0.79,30,19467,0.64,'Peking University'),
    (5,'MG76588',0.78,32,15417,0.72,'Guangdong University of Science and Technology'),
    (6,'JW40109',0.77,47,12598,0.84,''),
    (7,'CH42645',0.76,33,10298,0.60,'South China Normal University'),
    (8,'CW16048',0.73,47,10979,0.85,'Harbin Institute of Technology'),
    (9,'HL19556',0.72,47,11558,0.85,''),
    (10,'Leslie Cheung',0.72,47,8098,0.54,''),
    (11,'YW70391',0.72,28,9745,0.51,'Chongqing University of Technology'),
    (12,'PF72535',0.70,20,11309,0.65,''),
    (13,'HL14389',0.69,48,11886,0.87,'Harbin Institute of Technology'),
    (14,'XP53031',0.69,21,13600,0.74,'Tsinghua University'),
    (15,'YL36885',0.69,19,12687,0.72,''),
    (16,'Shao Fei',0.69,8,21385,0.50,'Nanjing University of Science and Technology'),
    (17,'LY76923',0.69,13,15103,0.62,''),
    (18,'YY54474',0.68,47,10147,0.85,''),
    (19,'WW60183',0.68,12,10606,0.39,'Harbin Institute of Technology'),
    (20,'WL77079',0.68,47,11717,0.87,''),
    (21,'XW31386',0.68,12,11951,0.59,''),
    (22,'QJ87786',0.68,9,11387,0.44,''),
    (23,'XW95492',0.67,6,14036,0.51,'Fudan University'),
    (24,'yuantaotao',0.67,21,14085,0.79,''),
    (25,'SJ63724',0.66,20,16170,0.79,''),
    (26,'CY21614',0.66,40,9880,0.83,''),
    (27,'TT70501',0.66,6,12604,0.53,''),
    (28,'CC99196',0.66,27,9172,0.59,''),
    (29,'YZ41300',0.66,9,11771,0.59,''),
    (30,'XD58255',0.66,10,12887,0.64,'Academy for Information Technology'),
]
me = (75, 0.59, 27, 8827, 0.71)
print(record('2026-09-23', rows, me, src='screenshot_1336'))
