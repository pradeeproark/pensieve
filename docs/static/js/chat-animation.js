/**
 * Chat Animation - Typewriter effect for conversation demos
 */

class ChatAnimator {
    constructor(storyElement) {
        this.story = storyElement;
        this.turns = Array.from(storyElement.querySelectorAll('.story-turn'));
        this.currentTurn = 0;
        this.isPlaying = false;
        this.speed = 0.5;

        // Store original content
        this.turnData = this.turns.map(turn => ({
            element: turn,
            role: turn.classList.contains('user') ? 'user' : 'assistant',
            content: turn.innerHTML,
            codeBlocks: []
        }));

        this.init();
    }

    init() {
        // Hide all turns initially
        this.turns.forEach(turn => {
            turn.style.display = 'none';
        });

        // Create controls
        this.createControls();
    }

    createControls() {
        const controls = document.createElement('div');
        controls.className = 'chat-controls';
        controls.innerHTML = `
            <button class="chat-btn play-btn" title="Play">▶ Play</button>
            <button class="chat-btn skip-btn" title="Skip to end">⏭ Skip</button>
            <label class="speed-control">
                Speed: <input type="range" min="0.5" max="3" step="0.5" value="0.5" class="speed-slider">
                <span class="speed-value">0.5x</span>
            </label>
        `;

        this.story.parentElement.insertBefore(controls, this.story);

        // Bind events
        controls.querySelector('.play-btn').addEventListener('click', () => this.togglePlay());
        controls.querySelector('.skip-btn').addEventListener('click', () => this.skipToEnd());
        controls.querySelector('.speed-slider').addEventListener('input', (e) => {
            this.speed = parseFloat(e.target.value);
            controls.querySelector('.speed-value').textContent = this.speed + 'x';
        });

        this.controls = controls;
        this.playBtn = controls.querySelector('.play-btn');
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        this.isPlaying = true;
        this.playBtn.textContent = '⏸ Pause';
        this.animateNextTurn();
    }

    pause() {
        this.isPlaying = false;
        this.playBtn.textContent = '▶ Play';
    }

    skipToEnd() {
        this.pause();
        this.turns.forEach((turn, i) => {
            turn.style.display = 'block';
            turn.innerHTML = this.turnData[i].content;
            turn.classList.remove('typing');
        });
        this.currentTurn = this.turns.length;
        this.playBtn.textContent = '↻ Replay';
    }

    async animateNextTurn() {
        if (!this.isPlaying || this.currentTurn >= this.turns.length) {
            if (this.currentTurn >= this.turns.length) {
                this.playBtn.textContent = '↻ Replay';
                this.currentTurn = 0;
            }
            this.isPlaying = false;
            return;
        }

        const turnData = this.turnData[this.currentTurn];
        const turn = turnData.element;

        turn.style.display = 'block';
        turn.classList.add('typing');

        await this.animateTurn(turn, turnData);

        turn.classList.remove('typing');
        this.currentTurn++;

        // Pause between turns
        await this.delay(500 / this.speed);

        this.animateNextTurn();
    }

    async animateTurn(turn, turnData) {
        const content = turnData.content;
        const role = turnData.role;

        // Parse content to separate code blocks from text
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;

        // Get role header
        const roleDiv = tempDiv.querySelector('.role');
        const roleHtml = roleDiv ? roleDiv.outerHTML : '';

        // Remove role div to process rest
        if (roleDiv) roleDiv.remove();

        // Start with role
        turn.innerHTML = roleHtml;

        // Process remaining content
        const children = Array.from(tempDiv.childNodes);

        for (const child of children) {
            if (!this.isPlaying) break;

            if (child.nodeType === Node.TEXT_NODE) {
                // Animate text
                await this.typeText(turn, child.textContent, role);
            } else if (child.nodeName === 'PRE' || child.nodeName === 'DIV') {
                // Code blocks and divs appear instantly
                turn.appendChild(child.cloneNode(true));
                this.scrollToBottom();
                await this.delay(300 / this.speed);
            } else if (child.nodeName === 'P') {
                // Animate paragraph content
                const p = document.createElement('p');
                turn.appendChild(p);
                await this.typeText(p, child.textContent, role);
            } else {
                // Other elements appear instantly
                turn.appendChild(child.cloneNode(true));
                this.scrollToBottom();
            }
        }
    }

    async typeText(container, text, role) {
        const baseDelay = role === 'user' ? 40 : 15; // Users type slower

        for (let i = 0; i < text.length; i++) {
            if (!this.isPlaying) break;

            container.innerHTML += text[i];
            this.scrollToBottom();

            // Variable delay for natural feel
            let delay = baseDelay / this.speed;
            if (text[i] === ' ') delay *= 0.5;
            if (text[i] === '.' || text[i] === '\n') delay *= 3;

            await this.delay(delay);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    scrollToBottom() {
        this.story.scrollTop = this.story.scrollHeight;
    }
}

/**
 * ScrollPlayManager - Manages scroll-triggered autoplay for demo sessions
 */
class ScrollPlayManager {
    constructor() {
        this.animators = new Map();
        this.observer = null;
        this.options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.25  // Trigger at 25% visibility
        };
    }

    init() {
        const sessions = document.querySelectorAll('.demo-session');

        // Create intersection observer
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            this.options
        );

        // Initialize and observe each session
        sessions.forEach((session) => {
            const story = session.querySelector('.story');
            if (story) {
                const animator = new ChatAnimator(story);
                this.animators.set(session, animator);
                this.observer.observe(session);
            }
        });
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            const animator = this.animators.get(entry.target);
            if (!animator) return;

            if (entry.isIntersecting) {
                // Scrolled into view - play if not already playing
                if (!animator.isPlaying && animator.currentTurn < animator.turns.length) {
                    setTimeout(() => animator.play(), 300);
                }
            } else {
                // Scrolled out of view - pause
                if (animator.isPlaying) {
                    animator.pause();
                }
            }
        });
    }
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if ('IntersectionObserver' in window) {
        // Modern browsers: scroll-triggered autoplay
        const manager = new ScrollPlayManager();
        manager.init();
    } else {
        // Fallback: initialize without scroll trigger, autoplay first only
        const stories = document.querySelectorAll('.story');
        stories.forEach((story, index) => {
            const animator = new ChatAnimator(story);
            if (index === 0) {
                setTimeout(() => animator.play(), 500);
            }
        });
    }
});
