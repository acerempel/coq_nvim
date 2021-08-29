(function(...)
  local iter = nil
  iter = function(root)
    return coroutine.wrap(
      function()
        if root:child_count() == 0 then
          coroutine.yield(root)
        else
          for node in root:iter_children() do
            for n in iter(node) do
              coroutine.yield(n)
            end
          end
        end
      end
    )
  end

  local iter_nodes = function()
    return coroutine.wrap(
      function()
        local go, parser = pcall(vim.treesitter.get_parser)
        if go then
          local trees = parser:parse()

          for _, tree in ipairs(trees) do
            for node in iter(tree:root()) do
              coroutine.yield(node)
            end
          end
        end
      end
    )
  end

  COQts_req = function(session, pos)
    vim.schedule(
      function()
        local acc = {}
        for node in iter_nodes() do
          if not node:missing() and not node:has_error() then
            table.insert(
              acc,
              {text = vim.treesitter.get_node_text(node, 0), kind = node:type()}
            )
          end
        end
        COQts_notify(session, acc)
      end
    )
  end
end)(...)
