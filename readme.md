# 命令格式定义


## width 命令
width命令用于修改指定道路部分或全部车道的宽度，并可做批量修改。

width命令包含以下参数：
1. **id**：修改的道路id号，必须输入。
2. **v**: 输入值，必须输入。
3. **s**: 是否平滑与其它道路连接边缘，默认为0。1和2为两种不同的平滑模式。
4. **ms**: 修改相连的更多道路数量，默认为0。
5. **sh**: 是否仅修改同向的其它道路，仅在ms!=0时有意义。默认为False。
6. **li**: 车道信息，默认为空，即修改所有车道段的所有车道。示例：li=-1,1,2
   
*注：由于数据集中所有道路仅含一个车道段，默认修改第一个车道段。*
*注：同时修改多条车道时，增加/减少的宽度为道路的总宽度，而非单个车道的宽度。*
*注：乘法模式被废弃，由于修改多条相连道路时的潜在冲突。*

## slope 命令
slope命令用于修改指定道路的坡度，并可做批量修改。

slope命令包含以下参数：
1. **id**：修改的道路id号，必须输入。
2. **v**: 输入值，必须输入。
3. **m**: 修改模式，分为add加法和mul乘法。
4. **mv**: 改变道路指定端高度。0表示首尾同时改变，1表示尾部，2表示头部。
5. **s**: 是否平滑与其它道路连接边缘，默认为0。（待完成）
6. **ms**: 抬升/下沉相连的更多道路数量，默认为0。
7. **sh**: 是否仅抬升/下沉同向的其它道路，仅在ms!=0时有意义。默认为False。


## curve 命令
curve命令用于修改指定道路的形状。
命令首先将道路拟合为一条三次贝塞尔曲线，该曲线有两个控制点L0和L1，通过改变控制点的位置对曲线的形状进行修改。

设道路起点O0到终点O1的距离为L，
点L0在以道路起点O0为原点的极坐标系中坐标为(p0, l0)，修改后，L0的坐标为（p0+h0, l0+L*v0）
点L1在以道路起点O1为原点的极坐标系中坐标为(p1, l1)，修改后，L1的坐标为（p1+h1, l1+L*v1）

*注：过高的v值与h值一般来讲是无意义的。*
1. **id**：修改的道路id号，必须输入。
2. **v0**: 参数。
3. **v1**: 参数。
4. **h0**: 参数。
5. **h1**: 参数。
   
## position 命令
position 命令用于修改指定道路起点或终点的位置。

*TODO:待完成。*
