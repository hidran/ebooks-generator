-- Paperback only: Word ignores the CSS classes the EPUB uses for callouts,
-- so give callout and chapter-opener titles a visible bold run instead.
function Span(el)
  if el.classes:includes("callout-title") then
    return pandoc.Strong(el.content)
  end
end
