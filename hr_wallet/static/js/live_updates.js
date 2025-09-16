// Live Updates for Employee Portal
class EmployeePortalLiveUpdates {
    constructor() {
        this.updateInterval = 30000; // 30 seconds
        this.isActive = true;
        this.init();
    }

    init() {
        // Start live updates when page loads
        this.startLiveUpdates();
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopLiveUpdates();
            } else {
                this.startLiveUpdates();
            }
        });

        // Add refresh buttons
        this.addRefreshButtons();
    }

    startLiveUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.isActive = true;
        this.updateDashboardStats();
        
        this.intervalId = setInterval(() => {
            if (this.isActive) {
                this.updateDashboardStats();
                this.updateRecentAttendance();
            }
        }, this.updateInterval);
    }

    stopLiveUpdates() {
        this.isActive = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    async updateDashboardStats() {
        try {
            const response = await fetch('/employee-portal/api/dashboard-stats/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDashboardElements(data);
                this.showUpdateIndicator('Dashboard updated');
            }
        } catch (error) {
            console.error('Error updating dashboard stats:', error);
        }
    }

    async updateRecentAttendance() {
        try {
            const response = await fetch('/employee-portal/api/recent-attendance/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateAttendanceTable(data.attendance_records);
            }
        } catch (error) {
            console.error('Error updating attendance:', error);
        }
    }

    updateDashboardElements(data) {
        // Update hours worked
        const hoursElement = document.getElementById('hours-worked');
        if (hoursElement) {
            hoursElement.textContent = data.hours_worked.toFixed(1);
            this.animateUpdate(hoursElement);
        }

        // Update leave balance
        const leaveElement = document.getElementById('leave-balance');
        if (leaveElement) {
            leaveElement.textContent = data.leave_balance;
            this.animateUpdate(leaveElement);
        }

        // Update pending requests
        const pendingElement = document.getElementById('pending-requests');
        if (pendingElement) {
            pendingElement.textContent = data.pending_requests;
            this.animateUpdate(pendingElement);
        }

        // Update attendance percentage
        const attendanceElement = document.getElementById('attendance-percentage');
        if (attendanceElement) {
            attendanceElement.textContent = data.attendance_percentage + '%';
            this.animateUpdate(attendanceElement);
        }

        // Update leave balances
        const sickLeaveElement = document.getElementById('sick-leave-remaining');
        if (sickLeaveElement) {
            sickLeaveElement.textContent = data.sick_leave_remaining;
        }

        const personalLeaveElement = document.getElementById('personal-leave-remaining');
        if (personalLeaveElement) {
            personalLeaveElement.textContent = data.personal_leave_remaining;
        }
    }

    updateAttendanceTable(records) {
        const tableBody = document.getElementById('attendance-table-body');
        if (!tableBody || !records.length) return;

        let html = '';
        records.forEach(record => {
            const statusBadge = this.getStatusBadge(record.status);
            html += `
                <tr>
                    <td>${this.formatDate(record.date)}</td>
                    <td>${record.clock_in || '--'}</td>
                    <td>${record.clock_out || '--'}</td>
                    <td>${record.total_hours.toFixed(1)}h</td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }

    getStatusBadge(status) {
        const badges = {
            'present': '<span class="badge bg-success">Present</span>',
            'late': '<span class="badge bg-warning">Late</span>',
            'absent': '<span class="badge bg-danger">Absent</span>',
            'half_day': '<span class="badge bg-info">Half Day</span>'
        };
        return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
    }

    animateUpdate(element) {
        element.classList.add('updated');
        setTimeout(() => {
            element.classList.remove('updated');
        }, 1000);
    }

    showUpdateIndicator(message) {
        const indicator = document.getElementById('update-indicator');
        if (indicator) {
            indicator.textContent = message + ' - ' + new Date().toLocaleTimeString();
            indicator.style.opacity = '1';
            setTimeout(() => {
                indicator.style.opacity = '0.5';
            }, 2000);
        }
    }

    addRefreshButtons() {
        // Add refresh button to dashboard cards
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach(card => {
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'btn btn-sm btn-outline-primary refresh-btn';
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
            refreshBtn.title = 'Refresh Data';
            refreshBtn.onclick = () => this.updateDashboardStats();
            
            const cardHeader = card.querySelector('.card-header');
            if (cardHeader) {
                cardHeader.appendChild(refreshBtn);
            }
        });
    }

    // Profile update functionality
    async updateProfile(formData) {
        try {
            const response = await fetch('/employee-portal/api/update-profile/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                return true;
            } else {
                this.showAlert('error', data.message);
                return false;
            }
        } catch (error) {
            this.showAlert('error', 'Error updating profile: ' + error.message);
            return false;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Initialize live updates when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.employeePortalUpdates = new EmployeePortalLiveUpdates();
});

// CSS for update animations
const style = document.createElement('style');
style.textContent = `
    .updated {
        animation: highlight 1s ease-in-out;
    }
    
    @keyframes highlight {
        0% { background-color: #fff3cd; }
        100% { background-color: transparent; }
    }
    
    .refresh-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 10;
    }
    
    .card-header {
        position: relative;
    }
    
    #update-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        opacity: 0.5;
        transition: opacity 0.3s;
        z-index: 1000;
    }
`;
document.head.appendChild(style);
