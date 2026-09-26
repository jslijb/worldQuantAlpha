# -*- coding: utf-8 -*-
"""一次性：把 0924 16:05 截图（=0924 3AM EST 刷新榜）转录进 top30 日档"""
import sys
sys.path.insert(0, r'D:\Python\worldquant\_autologs')
from lb_record import record

rows = [
    (1,'YX42680',0.84,34,13077,0.53,''),
    (2,'CS35156',0.84,37,17312,0.65,'Chongqing University of Posts and Telecommunications'),
    (3,'FL70603',0.81,46,14110,0.82,'Peking University'),
    (4,'Ke Wang',0.79,29,19467,0.63,'Peking University'),
    (5,'MG76588',0.78,32,15417,0.72,'Guangdong University of Science and Technology'),
    (6,'JW40109',0.76,46,12598,0.84,''),
    (7,'CH42645',0.76,32,10298,0.59,'South China Normal University'),
    (8,'Leslie Cheung',0.75,48,8285,0.52,''),
    (9,'YW70391',0.72,28,9745,0.50,'Chongqing University of Technology'),
    (10,'HL19556',0.72,46,11558,0.86,''),
    (11,'CW16048',0.72,46,10979,0.85,'Harbin Institute of Technology'),
    (12,'PF72535',0.70,20,11309,0.65,''),
    (13,'HL14389',0.70,47,11886,0.88,'Harbin Institute of Technology'),
    (14,'XP53031',0.69,21,13600,0.74,'Tsinghua University'),
    (15,'LY76923',0.69,14,15208,0.62,''),
    (16,'YL36885',0.69,19,12687,0.72,''),
    (17,'Shao Fei',0.69,8,21385,0.50,'Nanjing University of Science and Technology'),
    (18,'WW60183',0.68,12,10606,0.38,'Harbin Institute of Technology'),
    (19,'XW31386',0.68,12,11951,0.58,''),
    (20,'WL77079',0.68,46,11717,0.88,''),
    (21,'YY54474',0.68,46,10147,0.86,''),
    (22,'CC99196',0.68,28,9250,0.57,''),
    (23,'QJ87786',0.68,9,11387,0.44,''),
    (24,'yuantaotao',0.67,21,14085,0.79,''),
    (25,'XW95492',0.67,6,14036,0.51,'Fudan University'),
    (26,'SJ63724',0.66,19,16170,0.78,''),
    (27,'CY21614',0.66,40,9842,0.84,''),
    (28,'YZ41300',0.66,9,11771,0.57,''),
    (29,'BX12838',0.65,49,10015,0.88,'Harbin Institute of Technology'),
    (30,'XD58255',0.65,10,12887,0.65,'Academy for Information Technology'),
]
me = (58, 0.61, 28, 8906, 0.70)
print(record('2026-09-24', rows, me, src='screenshot_1605'))
