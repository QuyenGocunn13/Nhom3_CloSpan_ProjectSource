def run_clospan(sequences, minsup):
    from collections import defaultdict

    def count_support(pattern, sequences):
        """Đếm support của pattern bằng cách tìm subsequence trong các chuỗi"""
        count = 0
        for seq in sequences:
            if is_subsequence(pattern, seq):
                count += 1
        return count

    def is_subsequence(pattern, sequence):
        """Kiểm tra pattern có là subsequence của sequence không"""
        seq_iter = iter(sequence)
        return all(any(item in seq_iter for item in pat) for pat in pattern)

    def build_projected_db(pattern, sequences):
        """Tạo projected database chứa các phần đuôi còn lại sau pattern"""
        projected = []
        for seq in sequences:
            seq_iter = iter(seq)
            for i, pat_item in enumerate(pattern):
                for item in seq_iter:
                    if item == pat_item:
                        break
                else:
                    break
            else:
                remaining = list(seq_iter)
                if remaining:
                    projected.append(remaining)
        return projected

    def is_closed(current_pattern, current_sup, closed_dict):
        """Kiểm tra xem pattern hiện tại có bị bao bởi pattern dài hơn cùng support không"""
        for other_pat, other_sup in closed_dict.items():
            if len(other_pat) > len(current_pattern) and other_sup == current_sup:
                if is_subsequence(current_pattern, other_pat):
                    return False
        return True

    def extend_pattern(prefix, projected_db, closed_dict):
        """Hàm đệ quy để mở rộng prefix"""
        items_count = defaultdict(int)

        # Đếm các item tiếp theo có thể xuất hiện
        for seq in projected_db:
            used = set()
            for itemset in seq:
                for item in itemset:
                    if item not in used:
                        items_count[frozenset([item])] += 1
                        used.add(item)

        for itemset_frozen, count in items_count.items():
            if count >= minsup:
                new_pattern = prefix + [list(itemset_frozen)]
                new_projected = build_projected_db(new_pattern, sequences)
                if is_closed(new_pattern, count, closed_dict):
                    closed_dict[tuple(tuple(i) for i in new_pattern)] = count
                extend_pattern(new_pattern, new_projected, closed_dict)

    # Bắt đầu
    closed_patterns = {}
    extend_pattern([], sequences, closed_patterns)
    return closed_patterns
