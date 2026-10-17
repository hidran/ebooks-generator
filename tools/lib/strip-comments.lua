-- Drop HTML comments (author notes such as <!-- VERIFY: ... --> or
-- <!-- TODO screenshot ... -->) so they never reach the EPUB or DOCX.
-- A comment containing "--" would also make the EPUB's XHTML invalid.
local function is_comment(el)
  return el.format:match("html") and el.text:match("^%s*<!%-%-.*%-%->%s*$")
end

function RawBlock(el)
  if is_comment(el) then return {} end
end

function RawInline(el)
  if is_comment(el) then return {} end
end
