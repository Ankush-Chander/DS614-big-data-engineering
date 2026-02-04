---
delivery date:
  - "[[2026-01-29]]"
  - "[[2026-01-30]]"
---

### In-Memory vs. Disk-Based Data Structures

#### In-Memory (RAM)
- **Access Model:** Byte-addressable. You can read/write any specific byte directly.
- **Speed:** Extremely fast (nanoseconds).
- **Constraint:** The main constraint is **computational complexity** (Big-O of CPU operations). We worry about how many comparisons we make.
- **Typical Structures:** Binary Search Trees (BST), AVL Trees, Red-Black Trees.
    - _Why they work here:_ These trees are "tall" and "thin." A node usually contains just one key and two pointers. Following a pointer to a child node is effectively free because it's just a memory address jump.

#### Disk-Based (HDD/SSD)

- **Access Model:** Block-addressable. You cannot read a single byte; you must fetch an entire "page" or "block" (typically 4KB, 8KB, or 16KB) into memory to read even one bit of it.
- **Speed:** Slow (milliseconds or microseconds). A disk seek is roughly 100,000x slower than a RAM access.
- **Constraint:** The main constraint is **I/O Operations** (Disk Seeks). We don't care if we do 100 extra CPU comparisons if it saves us _one_ trip to the disk.
- **The Problem with BSTs:** If you store a Red-Black Tree on a disk, every time you follow a pointer to a child, you might need to fetch a new disk block. Since binary trees are deep (height = $\log_2 N$), searching for a key could require dozens of disk seeks. This is unacceptably slow.
    

---

### 2. The Solution: The B-Tree

To solve the disk constraint, we need a tree that is **wide** and **shallow** rather than tall and thin.

A B-tree is a self-balancing tree designed specifically to maintain sorted data and allow searches, sequential access, insertions, and deletions in logarithmic time, _while minimizing disk I/O_.

#### Key Characteristics

1. **High Fan-out:** Unlike a binary tree (which has 2 children), a B-tree node can have hundreds or thousands of children. This dramatically reduces the height of the tree.  
2. **Fat Nodes:** Each node is designed to fit exactly inside one disk page (e.g., 4KB).  
3. **Multiple Keys per Node:** Instead of 1 key, a node contains an ordered array of keys (e.g., 100 keys).  
    

#### How it optimizes for Disk

Imagine you want to find a number in a dataset of 1 billion items.  
- **Binary Tree:** Height is $\approx 30$. You might need **30 disk seeks**.  
- **B-Tree (Degree 1000):** Height is $\approx 3$. You only need **3 disk seeks**.  

When you load a B-Tree node, you get hundreds of keys in a single I/O operation. Once that node is in RAM, you can binary search those keys instantly (nanoseconds) to decide which child pointer to follow next.

---

**Mandatory reading(aligned with lecture)**:  [B-trees and database indexes — PlanetScale](https://planetscale.com/blog/btrees-and-database-indexes) 

---
## References
1. [B-trees and database indexes — PlanetScale](https://planetscale.com/blog/btrees-and-database-indexes) 
2. [Database Internals, Chapter 2](https://www.databass.dev/)
3. [Designing Data Intensive Applications, Chapter 3]()
