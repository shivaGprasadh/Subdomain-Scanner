// Handle form submission and progress updates
document.addEventListener('DOMContentLoaded', function() {
    const scanForm = document.getElementById('scan-form');
    const scanButton = document.getElementById('scan-button');
    const scanProgress = document.getElementById('scan-progress');
    const scanStatusMessage = document.getElementById('scan-status-message');
    
    // If we have an ongoing scan, check status immediately
    if (scanProgress.style.display !== 'none') {
        pollScanStatus();
    }
    
    // Handle form submission
    if (scanForm) {
        scanForm.addEventListener('submit', function(e) {
            // Show the progress indicator
            scanButton.disabled = true;
            scanButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scanning...';
            scanProgress.style.display = 'block';
            
            // Start polling for status updates
            setTimeout(pollScanStatus, 1000);
        });
    }
    
    // Function to poll the server for scan status
    function pollScanStatus() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // Update UI based on scan status
                if (data.scan_in_progress) {
                    // If scanning is still in progress, continue polling
                    setTimeout(pollScanStatus, 2000);
                    scanStatusMessage.textContent = `Scanning subdomains. Found ${data.total_count} so far (${data.active_count} active, ${data.inactive_count} inactive)...`;
                } else {
                    // Scan completed or encountered an error
                    if (data.error_message) {
                        scanStatusMessage.textContent = 'Error: ' + data.error_message;
                        scanStatusMessage.classList.add('text-danger');
                    } else if (data.scan_completed) {
                        // Reload the page to show results
                        window.location.reload();
                    }
                    
                    // Re-enable the scan button
                    scanButton.disabled = false;
                    scanButton.innerHTML = '<i class="fas fa-search me-1"></i> Scan Subdomains';
                }
            })
            .catch(error => {
                console.error('Error checking scan status:', error);
                scanStatusMessage.textContent = 'Error checking scan status. Please try again.';
                scanStatusMessage.classList.add('text-danger');
                
                // Re-enable the scan button
                scanButton.disabled = false;
                scanButton.innerHTML = '<i class="fas fa-search me-1"></i> Scan Subdomains';
                
                // Hide progress after error
                setTimeout(() => {
                    scanProgress.style.display = 'none';
                }, 3000);
            });
    }
    
    // Set up recheck buttons
    setupRecheckButtons();
    
    // Function to set up recheck buttons
    function setupRecheckButtons() {
        console.log("Setting up recheck buttons");
        document.querySelectorAll('.recheck-button').forEach(button => {
            console.log("Found recheck button for:", button.getAttribute('data-domain'));
            
            button.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Recheck button clicked");
                
                const domain = this.getAttribute('data-domain');
                console.log("Rechecking domain:", domain);
                
                // Find the parent cell that contains this button
                const responseCell = this.parentElement;
                console.log("Response cell:", responseCell);
                
                const buttonSpinner = this.querySelector('.spinner-border');
                const buttonIcon = this.querySelector('.fa-sync-alt');
                
                // Disable button and show spinner
                this.disabled = true;
                if (buttonIcon) buttonIcon.style.display = 'none';
                if (buttonSpinner) buttonSpinner.style.display = 'inline-block';
                
                // Make the API call to recheck the domain
                console.log("Sending request to:", `/recheck/${domain}`);
                fetch(`/recheck/${domain}`, {
                    method: 'POST'
                })
                .then(response => {
                    console.log("Got response:", response);
                    return response.json();
                })
                .then(data => {
                    console.log("Response data:", data);
                    if (data.success) {
                        // Update all instances of this domain's response cells
                        document.querySelectorAll(`[id="response-${domain}"]`).forEach(cell => {
                            // Keep only the text content from the first text node (remove any existing buttons or other elements)
                            const originalTextNode = Array.from(cell.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
                            if (originalTextNode) {
                                originalTextNode.textContent = data.response_info;
                            } else {
                                const textNode = document.createTextNode(data.response_info);
                                cell.insertBefore(textNode, cell.firstChild);
                            }
                            
                            // Briefly highlight the updated cell
                            cell.classList.add('bg-light');
                            setTimeout(() => {
                                cell.classList.remove('bg-light');
                            }, 2000);
                            
                            // If the response is no longer "No response", hide all recheck buttons for this domain
                            if (data.response_info !== "No response") {
                                const buttons = cell.querySelectorAll('.recheck-button');
                                buttons.forEach(btn => btn.style.display = 'none');
                            }
                        });
                    } else {
                        console.error("Error from server:", data.error);
                        alert('Error: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error rechecking domain:', error);
                    alert('Error rechecking domain. Please try again.');
                })
                .finally(() => {
                    // Re-enable button and hide spinner
                    this.disabled = false;
                    if (buttonIcon) buttonIcon.style.display = 'inline-block';
                    if (buttonSpinner) buttonSpinner.style.display = 'none';
                });
            });
        });
    }
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
