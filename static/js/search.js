// NASA Bioscience Explorer - Search Functionality

class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.suggestionsContainer = document.getElementById('suggestions');
        this.searchForm = document.getElementById('searchForm');
        this.debounceTimer = null;

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Search input events
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.hideSuggestions();
                }
            });

            this.searchInput.addEventListener('focus', () => {
                const query = this.searchInput.value.trim();
                if (query.length >= 2) {
                    this.showSuggestions(query);
                }
            });
        }

        // Quick search buttons
        const quickSearchButtons = document.querySelectorAll('.quick-search');
        quickSearchButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                if (this.searchInput) {
                    this.searchInput.value = query;
                    this.searchForm.submit();
                }
            });
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideSuggestions();
            }
        });

        // Form submission
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                const query = this.searchInput.value.trim();
                if (!query) {
                    e.preventDefault();
                    this.showError('Please enter a search term');
                    return;
                }

                this.showLoading();
            });
        }
    }

    handleSearchInput(query) {
        // Clear existing timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Debounce search suggestions
        this.debounceTimer = setTimeout(() => {
            if (query.length >= 2) {
                this.showSuggestions(query);
            } else {
                this.hideSuggestions();
            }
        }, 300);
    }

    async showSuggestions(query) {
        if (!this.suggestionsContainer) return;

        try {
            // For now, show some predefined suggestions based on common space biology terms
            const suggestions = this.getStaticSuggestions(query);

            if (suggestions.length > 0) {
                this.renderSuggestions(suggestions);
                this.suggestionsContainer.style.display = 'block';
            } else {
                this.hideSuggestions();
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.hideSuggestions();
        }
    }

    getStaticSuggestions(query) {
        const commonTerms = [
            'microgravity', 'space flight', 'cell biology', 'radiation',
            'bone density', 'muscle atrophy', 'plant biology', 'protein',
            'gene expression', 'immune system', 'metabolism', 'oxidative stress',
            'cardiovascular', 'neural', 'development', 'growth',
            'space station', 'astronaut', 'biomarker', 'tissue',
            'molecular', 'cellular', 'physiological', 'biological'
        ];

        const queryLower = query.toLowerCase();
        return commonTerms
            .filter(term => term.includes(queryLower))
            .slice(0, 6);
    }

    renderSuggestions(suggestions) {
        const html = suggestions.map(suggestion =>
            `<button type="button" class="btn btn-outline-secondary btn-sm suggestion-item" 
                     onclick="searchManager.selectSuggestion('${suggestion}')">
                ${suggestion}
            </button>`
        ).join(' ');

        this.suggestionsContainer.innerHTML = `
            <div class="d-flex flex-wrap gap-2">
                ${html}
            </div>
        `;
    }

    selectSuggestion(suggestion) {
        if (this.searchInput) {
            this.searchInput.value = suggestion;
            this.hideSuggestions();
            this.searchForm.submit();
        }
    }

    hideSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'none';
        }
    }

    showLoading() {
        const submitBtn = this.searchForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Searching...
            `;
            submitBtn.disabled = true;

            // Restore button after a delay (in case of slow response)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 10000);
        }
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.querySelector('.search-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger search-error mt-2';
            this.searchForm.appendChild(errorDiv);
        }

        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        `;

        // Remove error after 3 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 3000);
    }
}

// Search Results Page Functionality
class SearchResults {
    constructor() {
        this.initializeResultsPage();
    }

    initializeResultsPage() {
        // Add fade-in animation to results
        const results = document.querySelectorAll('.publication-card');
        results.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });

        // Track result clicks
        const exploreButtons = document.querySelectorAll('.publication-card a');
        exploreButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.trackClick(e.target.closest('.publication-card'));
            });
        });
    }

    trackClick(card) {
        // Add clicked state
        card.style.opacity = '0.7';
        setTimeout(() => {
            card.style.opacity = '1';
        }, 200);
    }
}

// Utility Functions
function highlightText(text, query) {
    if (!query || !text) return text;

    const words = query.toLowerCase().split(' ');
    let highlightedText = text;

    words.forEach(word => {
        if (word.length > 2) {
            const regex = new RegExp(`(${word})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        }
    });

    return highlightedText;
}

function formatResultsCount(count) {
    if (count === 0) return 'No results';
    if (count === 1) return '1 result';
    if (count < 1000) return `${count} results`;
    return `${(count / 1000).toFixed(1)}k results`;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search manager
    window.searchManager = new SearchManager();

    // Initialize search results if on results page
    if (document.querySelector('.publication-card')) {
        window.searchResults = new SearchResults();
    }

    // Add smooth scrolling to anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SearchManager, SearchResults };
}