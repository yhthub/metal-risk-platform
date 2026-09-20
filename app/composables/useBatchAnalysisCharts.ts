/**
 * 群体数据真实统计图表渲染器。
 * 仅负责将后端分析结果转换为现有 ECharts 视觉风格，不在前端重复计算统计口径。
 */
export const renderBatchAnalysisCharts = (analysis: any, echarts: any) => {
  const charts: any[] = []
  if (!analysis) return charts

  const createChart = (id: string, option: any) => {
    const element = document.getElementById(id)
    if (!element) return
    const chart = echarts.init(element, null, {
      devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2)
    })
    chart.setOption({
      animationDuration: 900,
      animationDurationUpdate: 500,
      animationEasing: 'cubicOut',
      textStyle: {
        color: '#475569',
        fontFamily: 'Inter, "Microsoft YaHei", sans-serif'
      },
      ...option
    })
    charts.push(chart)
  }

  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
  const axisLine = { show: false }
  const splitLine = { lineStyle: { type: 'dashed', color: '#E2E8F0' } }
  const tooltipStyle = {
    backgroundColor: 'rgba(255, 255, 255, 0.96)',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    padding: [10, 12],
    textStyle: { color: '#334155', fontSize: 12 },
    extraCssText: 'box-shadow: 0 10px 28px rgba(15, 23, 42, 0.12); border-radius: 8px;'
  }
  const verticalGradient = (start: string, end: string) =>
    new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: start },
      { offset: 1, color: end }
    ])
  const horizontalGradient = (start: string, end: string) =>
    new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: start },
      { offset: 1, color: end }
    ])

  const correlation = analysis.correlation
  const correlationData: any[] = []
  correlation.matrix.forEach((row: any[], y: number) => {
    row.forEach((value: number | null, x: number) => {
      correlationData.push([x, y, value])
    })
  })
  createChart('batchChartCorr', {
    tooltip: {
      ...tooltipStyle,
      position: 'top',
      formatter: (params: any) => {
        const [x, y, value] = params.data
        return `${correlation.labels[y]} × ${correlation.labels[x]}<br/>Pearson r: ${value ?? 'NA'}`
      }
    },
    grid: { left: '12%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: correlation.labels, axisLine, axisTick: { show: false } },
    yAxis: { type: 'category', data: correlation.labels, axisLine, axisTick: { show: false } },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      itemWidth: 12,
      itemHeight: 140,
      show: false,
      inRange: { color: ['#FCA5A5', '#FFF7ED', '#F8FAFC', '#93C5FD', '#1E3A8A'] }
    },
    series: [{
      type: 'heatmap',
      data: correlationData,
      label: {
        show: true,
        formatter: (params: any) => params.data[2]?.toFixed(2) ?? 'NA',
        color: (params: any) => Math.abs(params.data[2] || 0) >= 0.5 ? '#FFFFFF' : '#334155',
        fontSize: 10,
        fontWeight: 'bold'
      },
      itemStyle: { borderWidth: 3, borderColor: '#fff', borderRadius: 5 },
      emphasis: {
        itemStyle: {
          shadowBlur: 14,
          shadowColor: 'rgba(30, 58, 138, 0.24)'
        }
      }
    }]
  })

  const quartiles = analysis.quartiles
  createChart('batchChartQuartile', {
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10, fontWeight: 600 } },
    grid: { left: '16%', right: '5%', bottom: '15%', top: '20%' },
    xAxis: {
      type: 'category',
      data: quartiles.labels,
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold' }
    },
    yAxis: {
      type: 'log',
      name: '原始浓度（对数轴）',
      splitLine
    },
    series: [
      {
        name: 'Q1',
        type: 'bar',
        data: quartiles.q1,
        barMaxWidth: 20,
        itemStyle: { color: verticalGradient('#DBEAFE', '#93C5FD'), borderRadius: [4, 4, 0, 0] }
      },
      {
        name: '中位数',
        type: 'bar',
        data: quartiles.median,
        barMaxWidth: 20,
        itemStyle: { color: verticalGradient('#60A5FA', '#2563EB'), borderRadius: [4, 4, 0, 0] }
      },
      {
        name: 'Q3',
        type: 'bar',
        data: quartiles.q3,
        barMaxWidth: 20,
        itemStyle: { color: verticalGradient('#3B82F6', '#1E3A8A'), borderRadius: [4, 4, 0, 0] }
      }
    ]
  })

  const boxplot = analysis.boxplot
  createChart('batchChartBoxplot', {
    tooltip: { ...tooltipStyle, trigger: 'item', axisPointer: { type: 'shadow' } },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '12%' },
    xAxis: {
      type: 'category',
      data: boxplot.labels,
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold' }
    },
    yAxis: { type: 'value', name: '标准化 Z-Score', splitLine },
    series: [
      {
        name: '分布范围',
        type: 'boxplot',
        data: boxplot.values,
        itemStyle: { color: '#EFF6FF', borderColor: '#3B82F6', borderWidth: 2 },
        emphasis: { itemStyle: { borderColor: '#1D4ED8', borderWidth: 3 } }
      },
      {
        name: '离群点',
        type: 'scatter',
        data: boxplot.outliers,
        symbolSize: 5,
        itemStyle: { color: '#EF4444', opacity: 0.7 }
      }
    ]
  })

  const pca = analysis.pca
  const pcaGroups = ['正常血压组', '高血压组']
  createChart('batchChartPCA', {
    tooltip: {
      ...tooltipStyle,
      trigger: 'item',
      formatter: (params: any) => `${params.seriesName}<br/>PC1: ${params.data[0]}<br/>PC2: ${params.data[1]}`
    },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
    grid: { left: '15%', right: '10%', bottom: '15%', top: '18%' },
    xAxis: {
      type: 'value',
      name: `PC1 (${pca.explained_variance[0]}%)`,
      scale: true,
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: `PC2 (${pca.explained_variance[1]}%)`,
      scale: true,
      splitLine
    },
    series: pcaGroups.map((group, index) => ({
      type: 'scatter',
      name: group,
      data: pca.points
        .filter((point: any) => point.group === group)
        .map((point: any) => [point.x, point.y]),
      symbolSize: 8,
      itemStyle: {
        color: index === 0 ? '#10B981' : '#EF4444',
        opacity: 0.62,
        borderColor: '#FFFFFF',
        borderWidth: 1
      }
    }))
  })

  const completeness = analysis.completeness
  createChart('batchChartMissing', {
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '18%' },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%' },
      splitLine
    },
    yAxis: {
      type: 'category',
      data: completeness.map((item: any) => item.label),
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold' }
    },
    series: [
      {
        name: '有效数值',
        type: 'bar',
        stack: 'total',
        barWidth: '40%',
        itemStyle: { color: horizontalGradient('#6EE7B7', '#10B981') },
        label: {
          show: true,
          position: 'insideRight',
          formatter: '{c}%',
          color: '#fff'
        },
        data: completeness.map((item: any) => item.valid_rate)
      },
      {
        name: '缺失/非数值',
        type: 'bar',
        stack: 'total',
        barWidth: '40%',
        itemStyle: { color: horizontalGradient('#FCA5A5', '#EF4444'), borderRadius: [0, 4, 4, 0] },
        data: completeness.map((item: any) => +(100 - item.valid_rate).toFixed(2))
      }
    ]
  })

  const density = analysis.density
  createChart('batchChartDensity', {
    tooltip: { ...tooltipStyle, trigger: 'axis' },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '20%' },
    xAxis: {
      type: 'category',
      data: density.series[0]?.x || [],
      name: '标准化浓度（σ）',
      axisLabel: { interval: 4 }
    },
    yAxis: { type: 'value', name: '概率密度', splitLine },
    series: density.series.map((item: any, index: number) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: item.values,
      itemStyle: { color: colors[index] },
      lineStyle: { width: 2.2 },
      areaStyle: {
        color: verticalGradient(
          `${colors[index]}55`,
          `${colors[index]}05`
        )
      },
      emphasis: { focus: 'series', lineStyle: { width: 3.5 } }
    }))
  })

  const histogram = analysis.histogram
  createChart('batchChartParallel', {
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { type: 'scroll', top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '20%' },
    xAxis: {
      type: 'category',
      data: histogram.labels,
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold', fontSize: 10, rotate: 20 }
    },
    yAxis: { type: 'value', name: '样本数（人）', splitLine },
    series: histogram.series.map((item: any, index: number) => ({
      name: item.name,
      type: 'bar',
      data: item.values,
      barMaxWidth: 18,
      itemStyle: {
        color: verticalGradient(`${colors[index]}CC`, colors[index]),
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: `${colors[index]}55` } }
    }))
  })

  const bubble = analysis.bubble
  const bubbleGroups = ['正常血压组', '高血压组']
  createChart('batchChartBubble', {
    tooltip: {
      ...tooltipStyle,
      formatter: (params: any) => {
        const [age, sbp, exposure, dbp] = params.data
        return `${params.seriesName}<br/>年龄: ${age} 岁<br/>平均血压: ${sbp}/${dbp} mmHg<br/>综合暴露百分位: P${exposure}`
      }
    },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10 },
    grid: { left: '15%', right: '10%', bottom: '15%', top: '18%' },
    xAxis: { type: 'value', name: '年龄（岁）', splitLine: { show: false } },
    yAxis: { type: 'value', name: '平均收缩压（mmHg）', splitLine },
    series: bubbleGroups.map((group, index) => ({
      type: 'scatter',
      name: group,
      data: bubble.points
        .filter((point: any) => point.group === group)
        .map((point: any) => [
          point.age,
          point.mean_sbp,
          point.exposure_percentile,
          point.mean_dbp
        ]),
      symbolSize: (data: number[]) => Math.max(9, Math.min(32, data[2] / 3)),
      itemStyle: {
        color: index === 0 ? 'rgba(59, 130, 246, 0.58)' : 'rgba(239, 68, 68, 0.7)',
        borderColor: '#fff',
        borderWidth: 1.5,
        shadowBlur: 8,
        shadowColor: index === 0 ? 'rgba(59, 130, 246, 0.25)' : 'rgba(239, 68, 68, 0.25)'
      },
      emphasis: { scale: 1.35 }
    }))
  })

  const demographics = analysis.demographics
  createChart('batchChartMarital', {
    tooltip: { ...tooltipStyle, trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: '2%',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, fontWeight: 600 }
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: true, formatter: '{b}\n{d}%', fontWeight: 'bold', fontSize: 11 },
      labelLine: { show: true, length: 8, length2: 12 },
      emphasis: {
        scaleSize: 8,
        label: { fontSize: 13, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 12, shadowColor: 'rgba(15, 23, 42, 0.18)' }
      },
      data: demographics.marital.map((item: any, index: number) => ({
        ...item,
        itemStyle: { color: colors[index % colors.length] }
      }))
    }]
  })

  createChart('batchChartEducation', {
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '28%', right: '13%', bottom: '10%', top: '10%' },
    xAxis: { type: 'value', name: '人数', splitLine },
    yAxis: {
      type: 'category',
      data: demographics.education.map((item: any) => item.name),
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold', fontSize: 10 }
    },
    series: [{
      type: 'bar',
      barWidth: '45%',
      data: demographics.education.map((item: any, index: number) => {
        const gradients = [
          ['#FCA5A5', '#EF4444'],
          ['#FCD34D', '#F59E0B'],
          ['#A7F3D0', '#10B981'],
          ['#93C5FD', '#3B82F6'],
          ['#C4B5FD', '#6366F1'],
          ['#DDD6FE', '#8B5CF6']
        ]
        const [start, end] = gradients[index % gradients.length]
        return {
          value: item.value,
          itemStyle: {
            color: horizontalGradient(start, end),
            borderRadius: [0, 5, 5, 0]
          }
        }
      }),
      label: {
        show: true,
        position: 'right',
        formatter: '{c} 人',
        color: '#475569',
        fontSize: 11,
        fontWeight: 'bold'
      }
    }]
  })

  createChart('batchChartIncome', {
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10 },
    grid: { left: '15%', right: '5%', bottom: '18%', top: '18%' },
    xAxis: {
      type: 'category',
      data: demographics.income.map((item: any) => item.name),
      axisTick: { show: false },
      axisLabel: { fontWeight: 'bold', fontSize: 10 }
    },
    yAxis: { type: 'value', name: '人数', splitLine },
    series: [
      {
        name: '男性',
        type: 'bar',
        stack: 'total',
        barWidth: '45%',
        data: demographics.income.map((item: any) => item.male),
        itemStyle: { color: '#3B82F6' },
        label: { show: true, color: '#FFFFFF', fontWeight: 'bold', fontSize: 10 }
      },
      {
        name: '女性',
        type: 'bar',
        stack: 'total',
        barWidth: '45%',
        data: demographics.income.map((item: any) => item.female),
        itemStyle: { color: '#EC4899', borderRadius: [4, 4, 0, 0] },
        label: { show: true, color: '#FFFFFF', fontWeight: 'bold', fontSize: 10 }
      }
    ]
  })

  return charts
}
