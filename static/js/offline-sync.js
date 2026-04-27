// Offline Sync Module for QR Attendance System
// Handles storing attendance when offline and syncing when online

class OfflineSync {
    constructor() {
        this.STORAGE_KEY = 'qr_attendance_pending';
        this.SYNC_STATUS_KEY = 'qr_attendance_sync_status';
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;
        
        this.init();
    }
    
    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Check initial status
        this.updateOnlineStatus();
        
        // Register for background sync if supported
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            this.registerBackgroundSync();
        }
        
        // Display pending count on load
        this.updatePendingUI();
        
        console.log('[OfflineSync] Initialized. Online:', this.isOnline);
    }
    
    // Register background sync
    async registerBackgroundSync() {
        try {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-attendance');
            console.log('[OfflineSync] Background sync registered');
        } catch (error) {
            console.error('[OfflineSync] Background sync registration failed:', error);
        }
    }
    
    // Update online status
    updateOnlineStatus() {
        this.isOnline = navigator.onLine;
        this.updateUI();
    }
    
    // Handle going online
    async handleOnline() {
        console.log('[OfflineSync] Back online');
        this.isOnline = true;
        this.updateUI();
        this.showToast('Connection restored. Syncing...', 'success');
        
        // Try to sync pending attendance
        await this.syncPendingAttendance();
        
        // Update sync status
        this.updateSyncStatus('online');
    }
    
    // Handle going offline
    handleOffline() {
        console.log('[OfflineSync] Gone offline');
        this.isOnline = false;
        this.updateUI();
        this.showToast('You are offline. Attendance will be saved locally.', 'warning');
        this.updateSyncStatus('offline');
    }
    
    // Queue attendance for submission
    async queueAttendance(attendanceData) {
        try {
            // Get existing queue
            const queue = this.getPendingQueue();
            
            // Add timestamp and ID
            attendanceData.id = this.generateId();
            attendanceData.queuedAt = new Date().toISOString();
            attendanceData.attempts = 0;
            
            // Add to queue
            queue.push(attendanceData);
            
            // Save to localStorage
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(queue));
            
            console.log('[OfflineSync] Attendance queued:', attendanceData.id);
            
            // Update UI
            this.updatePendingUI();
            
            // If online, try to sync immediately
            if (this.isOnline && !this.syncInProgress) {
                await this.syncPendingAttendance();
            }
            
            return {
                success: true,
                message: this.isOnline ? 'Submitting...' : 'Saved offline. Will sync when online.',
                id: attendanceData.id,
                isOffline: !this.isOnline
            };
        } catch (error) {
            console.error('[OfflineSync] Queue failed:', error);
            return {
                success: false,
                error: 'Failed to save attendance'
            };
        }
    }
    
    // Get pending queue
    getPendingQueue() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('[OfflineSync] Error reading queue:', error);
            return [];
        }
    }
    
    // Sync pending attendance
    async syncPendingAttendance() {
        if (this.syncInProgress || !this.isOnline) {
            return;
        }
        
        this.syncInProgress = true;
        console.log('[OfflineSync] Starting sync...');
        
        try {
            const queue = this.getPendingQueue();
            
            if (queue.length === 0) {
                console.log('[OfflineSync] No pending attendance');
                this.syncInProgress = false;
                return;
            }
            
            console.log(`[OfflineSync] Syncing ${queue.length} items...`);
            
            const successful = [];
            const failed = [];
            
            for (const item of queue) {
                try {
                    item.attempts++;
                    
                    const result = await this.submitAttendance(item);
                    
                    if (result.success) {
                        successful.push(item.id);
                        console.log('[OfflineSync] Synced:', item.id);
                    } else {
                        // If max attempts reached, mark as failed
                        if (item.attempts >= 3) {
                            failed.push(item);
                            console.error('[OfflineSync] Max attempts reached:', item.id);
                        } else {
                            // Will retry next time
                            console.log('[OfflineSync] Will retry:', item.id);
                        }
                    }
                } catch (error) {
                    console.error('[OfflineSync] Submit error:', error);
                    if (item.attempts >= 3) {
                        failed.push(item);
                    }
                }
            }
            
            // Remove successful items from queue
            const remainingQueue = queue.filter(
                item => !successful.includes(item.id) && !failed.find(f => f.id === item.id)
            );
            
            // Save remaining queue
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(remainingQueue));
            
            // Update UI
            this.updatePendingUI();
            
            // Show results
            if (successful.length > 0) {
                this.showToast(`Synced ${successful.length} attendance record(s)`, 'success');
            }
            
            if (failed.length > 0) {
                this.showToast(`${failed.length} record(s) failed to sync`, 'error');
            }
            
            console.log(`[OfflineSync] Sync complete. Success: ${successful.length}, Failed: ${failed.length}`);
            
        } catch (error) {
            console.error('[OfflineSync] Sync error:', error);
        } finally {
            this.syncInProgress = false;
        }
    }
    
    // Submit attendance to server
    async submitAttendance(data) {
        try {
            const response = await fetch('/api/scan-attendance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    qr_value: data.qr_value,
                    latitude: data.latitude,
                    longitude: data.longitude
                })
            });
            
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('[OfflineSync] Submit error:', error);
            return {
                success: false,
                error: 'Network error'
            };
        }
    }
    
    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    // Get CSRF token
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Update sync status in storage
    updateSyncStatus(status) {
        const syncStatus = {
            status: status,
            lastUpdate: new Date().toISOString()
        };
        localStorage.setItem(this.SYNC_STATUS_KEY, JSON.stringify(syncStatus));
    }
    
    // Get sync status
    getSyncStatus() {
        try {
            const data = localStorage.getItem(this.SYNC_STATUS_KEY);
            return data ? JSON.parse(data) : { status: 'unknown', lastUpdate: null };
        } catch (error) {
            return { status: 'unknown', lastUpdate: null };
        }
    }
    
    // Update pending count in UI
    updatePendingUI() {
        const queue = this.getPendingQueue();
        const count = queue.length;
        
        // Find all elements with data-pending-count attribute
        const elements = document.querySelectorAll('[data-pending-count]');
        elements.forEach(el => {
            el.textContent = count;
            el.style.display = count > 0 ? 'inline' : 'none';
        });
        
        // Find sync status indicators
        const statusElements = document.querySelectorAll('[data-sync-status]');
        statusElements.forEach(el => {
            if (this.isOnline) {
                el.className = 'badge bg-success';
                el.textContent = count > 0 ? `Syncing ${count}...` : 'Synced';
            } else {
                el.className = 'badge bg-warning';
                el.textContent = `Offline (${count} pending)`;
            }
        });
    }
    
    // Update UI based on online status
    updateUI() {
        const offlineElements = document.querySelectorAll('.offline-indicator');
        offlineElements.forEach(el => {
            el.style.display = this.isOnline ? 'none' : 'block';
        });
        
        this.updatePendingUI();
    }
    
    // Show toast notification
    showToast(message, type = 'info') {
        // Check if toast container exists
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : type === 'error' ? 'danger' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${type === 'success' ? 'bi-check-circle' : type === 'warning' ? 'bi-exclamation-triangle' : 'bi-info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // Force sync (can be called manually)
    async forceSync() {
        if (!this.isOnline) {
            this.showToast('Cannot sync while offline', 'warning');
            return;
        }
        
        this.showToast('Syncing now...', 'info');
        await this.syncPendingAttendance();
    }
    
    // Clear pending queue (for debugging)
    clearQueue() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updatePendingUI();
        console.log('[OfflineSync] Queue cleared');
    }
    
    // Get queue info (for debugging)
    getQueueInfo() {
        const queue = this.getPendingQueue();
        return {
            count: queue.length,
            items: queue,
            isOnline: this.isOnline,
            syncInProgress: this.syncInProgress
        };
    }
}

// Initialize on page load
let offlineSync;
document.addEventListener('DOMContentLoaded', () => {
    offlineSync = new OfflineSync();
    
    // Make available globally for debugging
    window.offlineSync = offlineSync;
});

// Expose to global scope
window.OfflineSync = OfflineSync;
