import ast

with open("alembic/versions/ace1590fc209_add_support_and_help_center_models.py", "r") as f:
    content = f.read()

tree = ast.parse(content)

class RemoveAlterColumn(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute):
                if func.attr == 'alter_column' and getattr(func.value, 'id', None) == 'batch_op':
                    return None
        return node
    
    def visit_With(self, node):
        self.generic_visit(node)
        # If the With block body is empty, we should remove the With block, or insert a pass.
        if not node.body:
            node.body = [ast.Pass()]
        return node

transformer = RemoveAlterColumn()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)

new_content = ast.unparse(new_tree)

with open("alembic/versions/ace1590fc209_add_support_and_help_center_models.py", "w") as f:
    f.write(new_content)
