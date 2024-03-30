use ignore::WalkBuilder;
use std::path::PathBuf;

pub fn get_embeddable_files(root: &str) -> Vec<PathBuf> {
    let mut files = Vec::new();

    // Walk the directory tree while respecting .gitignore rules.
    let walker = WalkBuilder::new(root)
        .ignore(true)
        .git_ignore(true)
        .git_exclude(true)
        .build()
        .flatten();

    for entry in walker {
        if let Ok(abs_path) = entry.path().canonicalize() {
            files.push(abs_path);
        }
    }

    files
}
