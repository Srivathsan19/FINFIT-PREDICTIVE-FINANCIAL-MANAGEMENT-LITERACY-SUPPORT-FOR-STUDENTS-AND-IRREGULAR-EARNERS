let expenseChartInstance = null;
let incomeExpenseChartInstance = null;

function createCustomLegend(labels, values, colors, total) {
    // Find or create legend container
    let legendContainer = document.getElementById('expense-chart-legend');
    if (!legendContainer) {
        const chartContainer = document.querySelector('.pie-chart-container');
        if (chartContainer && chartContainer.parentElement) {
            legendContainer = document.createElement('div');
            legendContainer.id = 'expense-chart-legend';
            legendContainer.style.cssText = `
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
                padding: 20px;
                margin-top: 15px;
                border-top: 1px solid ${document.body.classList.contains('light') ? '#e0e0e0' : '#333'};
            `;
            chartContainer.parentElement.insertBefore(legendContainer, chartContainer.nextSibling);
        } else {
            return; // Can't find container
        }
    }
    
    // Clear existing legend
    legendContainer.innerHTML = '';
    
    // Create legend items
    labels.forEach((label, i) => {
        const value = values[i];
        const percentage = ((value / total) * 100).toFixed(1);
        const color = colors[i % colors.length];
        
        const legendItem = document.createElement('div');
        legendItem.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: ${document.body.classList.contains('light') ? '#f8f9fa' : '#2d3436'};
            border-radius: 8px;
            border-left: 4px solid ${color};
            transition: transform 0.2s, box-shadow 0.2s;
        `;
        legendItem.onmouseenter = () => {
            legendItem.style.transform = 'translateX(5px)';
            legendItem.style.boxShadow = `0 4px 12px ${color}40`;
        };
        legendItem.onmouseleave = () => {
            legendItem.style.transform = 'translateX(0)';
            legendItem.style.boxShadow = 'none';
        };
        
        const colorDot = document.createElement('div');
        colorDot.style.cssText = `
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: ${color};
            flex-shrink: 0;
        `;
        
        const labelText = document.createElement('div');
        labelText.style.cssText = `
            flex: 1;
            min-width: 0;
        `;
        labelText.innerHTML = `
            <div style="font-weight: 600; color: ${document.body.classList.contains('light') ? '#181a1b' : '#f1f1f1'}; font-size: 13px; margin-bottom: 4px;">
                ${label}
            </div>
            <div style="font-size: 11px; color: ${document.body.classList.contains('light') ? '#666' : '#9aa0a6'};">
                ${formatCurrency(value)} • ${percentage}%
            </div>
        `;
        
        legendItem.appendChild(colorDot);
        legendItem.appendChild(labelText);
        legendContainer.appendChild(legendItem);
    });
}

function renderExpenseChart() {
    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            const categories = {};
            data.filter(t => t.type === 'expense').forEach(t => {
                categories[t.category] = (categories[t.category] || 0) + t.amount;
            });
            
            const ctx = document.getElementById('expenseChart');
            if (!ctx) return;
            
            // Destroy existing chart if it exists
            if (expenseChartInstance) {
                expenseChartInstance.destroy();
            }
            
            const labels = Object.keys(categories);
            const values = Object.values(categories);
            
            if (labels.length === 0) {
                ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
                const ctx2d = ctx.getContext('2d');
                ctx2d.fillStyle = '#888';
                ctx2d.font = '16px Arial';
                ctx2d.textAlign = 'center';
                ctx2d.fillText('No expense data yet', ctx.width / 2, ctx.height / 2);
            // Update center total to zero
            const centerEl = document.getElementById('pie-chart-total');
            if (centerEl) {
                const amountEl = centerEl.querySelector('.center-amount');
                if (amountEl) amountEl.textContent = '₹0.00';
            }
            // Clear legend if it exists
            const legendContainer = document.getElementById('expense-chart-legend');
            if (legendContainer) {
                legendContainer.innerHTML = '';
            }
                return;
            }
            
            const total = values.reduce((a, b) => a + b, 0);
            
            // Modern vibrant gradient color palette
            const vibrantColors = [
                '#667eea',  // Purple
                '#f093fb',  // Pink
                '#4facfe',  // Blue
                '#43e97b',  // Green
                '#fa709a',  // Coral
                '#30cfd0',  // Cyan
                '#a8edea',  // Mint
                '#ff9a9e',  // Rose
                '#ffecd2',  // Peach
                '#ff6e7f',  // Red
                '#764ba2',  // Deep Purple
                '#f5576c',  // Deep Pink
                '#00f2fe',  // Light Blue
                '#38f9d7',  // Light Green
                '#fee140'   // Yellow
            ];
            
            expenseChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: vibrantColors.slice(0, labels.length),
                        borderWidth: 4,
                        borderColor: document.body.classList.contains('light') ? '#ffffff' : '#1a1a1a',
                        hoverBorderWidth: 6,
                        hoverOffset: 12,
                        hoverBorderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 1500,
                        easing: 'easeOutQuart'
                    },
                    cutout: '60%',
                    layout: {
                        padding: {
                            left: 10,
                            right: 10,
                            top: 10,
                            bottom: 10
                        }
                    },
                    plugins: {
                        legend: {
                            display: false  // Hide default legend, we'll create a custom one
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 15,
                            titleFont: {
                                size: 16,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: 14
                            },
                            borderColor: 'rgba(255, 255, 255, 0.2)',
                            borderWidth: 1,
                            cornerRadius: 10,
                            displayColors: true,
                            callbacks: {
                                title: function(context) {
                                    return context[0].label;
                                },
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const percentage = ((value / total) * 100).toFixed(2);
                                    return [
                                        `Amount: ${formatCurrency(value)}`,
                                        `Percentage: ${percentage}%`,
                                        `Total: ${formatCurrency(total)}`
                                    ];
                                },
                                labelColor: function(context) {
                                    return {
                                        borderColor: context.dataset.backgroundColor[context.dataIndex],
                                        backgroundColor: context.dataset.backgroundColor[context.dataIndex]
                                    };
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
            
            // Create custom legend
            createCustomLegend(labels, values, vibrantColors, total);
            
            // Update center total
            setTimeout(() => {
                const centerEl = document.getElementById('pie-chart-total');
                if (centerEl) {
                    const amountEl = centerEl.querySelector('.center-amount');
                    if (amountEl) amountEl.textContent = formatCurrency(total);
                }
            }, 100);
        });
}

function renderIncomeExpenseChart() {
    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            const income = data.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
            const expense = data.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);
            
            const ctx = document.getElementById('incomeExpenseChart');
            if (!ctx) return;
            
            // Destroy existing chart if it exists
            if (incomeExpenseChartInstance) {
                incomeExpenseChartInstance.destroy();
            }
            
            incomeExpenseChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Income', 'Expenses'],
                    datasets: [{
                        label: 'Amount (₹)',
                        data: [income, expense],
                        backgroundColor: ['#00b894', '#e17055'],
                        borderColor: ['#00b894', '#e17055'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: document.body.classList.contains('light') ? '#181a1b' : '#f1f1f1'
                            },
                            grid: {
                                color: document.body.classList.contains('light') ? '#ddd' : '#333'
                            }
                        },
                        x: {
                            ticks: {
                                color: document.body.classList.contains('light') ? '#181a1b' : '#f1f1f1'
                            },
                            grid: {
                                color: document.body.classList.contains('light') ? '#ddd' : '#333'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        });
}