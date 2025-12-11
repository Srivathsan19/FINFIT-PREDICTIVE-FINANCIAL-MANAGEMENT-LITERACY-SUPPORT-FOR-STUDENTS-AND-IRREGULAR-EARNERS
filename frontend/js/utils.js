// Shared utility functions

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatCurrency(amount) {
    return `₹${amount.toFixed(2)}`;
}

// Handle authentication errors
function handleAuthError(response) {
    if (response.status === 401) {
        // User not authenticated, redirect to login
        if (typeof showLogin === 'function') {
            showLogin();
        }
        if (typeof updateAuthUI === 'function') {
            updateAuthUI();
        }
        return true;
    }
    return false;
}

function formatBotMessage(text) {
    if (!text) return '<p></p>';
    
    // First, handle code blocks (before escaping HTML)
    const codeBlocks = [];
    let codeBlockIndex = 0;
    text = text.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
        const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
        codeBlocks[codeBlockIndex] = { lang, code: code.trim() };
        codeBlockIndex++;
        return placeholder;
    });
    
    // Escape HTML (but preserve placeholders)
    let formatted = escapeHtml(text);
    
    // Restore code blocks
    codeBlocks.forEach((block, index) => {
        const code = escapeHtml(block.code);
        formatted = formatted.replace(`__CODE_BLOCK_${index}__`, `<pre><code>${code}</code></pre>`);
    });
    
    // Split into lines for processing
    const lines = formatted.split('\n');
    const processedLines = [];
    let inList = false;
    let listType = null; // 'ul' or 'ol'
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Skip empty lines (they'll become paragraph breaks)
        if (!line) {
            if (inList) {
                processedLines.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
            processedLines.push('');
            continue;
        }
        
        // Check for numbered list (1. item or 1) item)
        const numberedMatch = line.match(/^(\d+)[\.)]\s+(.+)$/);
        if (numberedMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) processedLines.push(`</${listType}>`);
                processedLines.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            processedLines.push(`<li>${numberedMatch[2]}</li>`);
            continue;
        }
        
        // Check for bullet list (-, *, •)
        const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
        if (bulletMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) processedLines.push(`</${listType}>`);
                processedLines.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            processedLines.push(`<li>${bulletMatch[1]}</li>`);
            continue;
        }
        
        // Not a list item - close list if open
        if (inList) {
            processedLines.push(`</${listType}>`);
            inList = false;
            listType = null;
        }
        
        // Regular line
        processedLines.push(line);
    }
    
    // Close any open list
    if (inList) {
        processedLines.push(`</${listType}>`);
    }
    
    // Join lines and handle paragraphs
    formatted = processedLines.join('\n');
    
    // Split by double newlines for paragraphs
    const paragraphs = formatted.split(/\n\n+/);
    formatted = paragraphs.map(para => {
        para = para.trim();
        if (!para) return '';
        
        // Don't wrap lists or code blocks in paragraphs
        if (para.startsWith('<ol>') || para.startsWith('<ul>') || para.startsWith('<pre>')) {
            return para;
        }
        
        // Format inline markdown
        // First handle inline code: `code`
        para = para.replace(/`([^`\n]+)`/g, '<code>$1</code>');
        // Then bold: **text**
        para = para.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Finally italic: *text* (only single asterisks that aren't part of **)
        // Split by existing HTML tags to avoid conflicts
        const parts = para.split(/(<[^>]+>)/);
        para = parts.map(part => {
            if (part.startsWith('<')) return part; // Already HTML tag
            return part.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
        }).join('');
        
        return `<p>${para}</p>`;
    }).filter(p => p).join('');
    
    return formatted || '<p></p>';
}


