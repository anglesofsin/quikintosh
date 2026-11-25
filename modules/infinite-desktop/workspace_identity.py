"""Resolve Hyprland workspace identity across numeric and named IPC formats."""


def workspace_identity(workspace):
    return workspace.get("id") or workspace.get("address") or workspace.get("name")
