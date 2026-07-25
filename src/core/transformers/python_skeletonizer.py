import ast
from core.interfaces.transformer_step import ITransformerStep


class PythonSkeletonizerStep(ITransformerStep):

    class _FunctionBodyReplacer(ast.NodeTransformer):

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            self.generic_visit(node)
            docstring = ast.get_docstring(node)
            new_body = []
            if docstring:
                new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
            new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
            node.body = new_body
            return node

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
            self.generic_visit(node)
            docstring = ast.get_docstring(node)
            new_body = []
            if docstring:
                new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
            new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
            node.body = new_body
            return node

    def transform(self, text: str, ext: str) -> str:
        if not text or ext.lower() != ".py":
            return text

        try:
            tree = ast.parse(text)
            transformed_tree = self._FunctionBodyReplacer().visit(tree)
            ast.fix_missing_locations(transformed_tree)
            return ast.unparse(transformed_tree)
        except Exception:
            return text