import os
import heapq

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Min-heap comparison based on frequency
    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCompressor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.codes = {}
        self.reverse_mapping = {}

    # Step 1: Calculate character frequencies
    def _make_frequency_dict(self, text):
        frequency = {}
        for character in text:
            if character not in frequency:
                frequency[character] = 0
            frequency[character] += 1
        return frequency

    # Step 2: Build Priority Queue (Min-Heap) and Huffman Tree
    def _build_huffman_tree(self, frequency):
        heap = []
        for key, freq in frequency.items():
            node = HuffmanNode(key, freq)
            heapq.heappush(heap, node)

        while len(heap) > 1:
            node1 = heapq.heappop(heap)
            node2 = heapq.heappop(heap)

            sum_freq = node1.freq + node2.freq
            merged_node = HuffmanNode(None, sum_freq)
            merged_node.left = node1
            merged_node.right = node2

            heapq.heappush(heap, merged_node)

        return heap[0] if heap else None

    # Step 3: Generate Prefix Codes via Recursive Tree Traversal
    def _make_codes_helper(self, node, current_code):
        if node is None:
            return

        if node.char is not None:
            self.codes[node.char] = current_code
            self.reverse_mapping[current_code] = node.char
            return

        self._make_codes_helper(node.left, current_code + "0")
        self._make_codes_helper(node.right, current_code + "1")

    def _generate_codes(self, root):
        current_code = ""
        self._make_codes_helper(root, current_code)

    # Step 4: Convert text into bit-string representation
    def _get_encoded_text(self, text):
        encoded_text = ""
        for char in text:
            encoded_text += self.codes[char]
        return encoded_text

    # Step 5: Pad bit-string to make its length a multiple of 8 (Byte alignment)
    def _pad_encoded_text(self, encoded_text):
        extra_padding = 8 - len(encoded_text) % 8
        for i in range(extra_padding):
            encoded_text += "0"

        padded_info = "{0:08b}".format(extra_padding)
        encoded_text = padded_info + encoded_text
        return encoded_text

    # Step 6: Convert bit-string to byte array for binary file writing
    def _get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            raise ValueError("Encoded text not padded properly")

        b_array = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i+8]
            b_array.append(int(byte, 2))
        return b_array

    # --- COMPRESSION FUNCTION ---
    def compress(self):
        filename, file_extension = os.path.splitext(self.file_path)
        output_path = filename + ".bin"

        with open(self.file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        if not text:
            print("Error: File is empty.")
            return

        # Execute Huffman pipeline
        frequency = self._make_frequency_dict(text)
        root = self._build_huffman_tree(frequency)
        self._generate_codes(root)

        encoded_text = self._get_encoded_text(text)
        padded_encoded_text = self._pad_encoded_text(encoded_text)
        bytes_array = self._get_byte_array(padded_encoded_text)

        # Write compressed binary data with the tree mapping header
        with open(output_path, 'wb') as output:
            # Simple header serialization: store frequency table length and data
            # For simplicity in pure python, we can store codes or tree state.
            # Here we serialize codes mapping using length-prefixed strings.
            header = str(self.codes).encode('utf-8')
            output.write(len(header).to_bytes(4, byteorder='big'))
            output.write(header)
            output.write(bytes(bytes_array))

        print(f"Compression successful! Output saved to: {output_path}")
        
        # Calculate size reduction metrics
        original_size = os.path.getsize(self.file_path)
        compressed_size = os.path.getsize(output_path)
        print(f"Original Size: {original_size} bytes | Compressed Size: {compressed_size} bytes")
        return output_path

    # --- DECOMPRESSION FUNCTION ---
    def decompress(self, input_binary_path):
        filename, _ = os.path.splitext(input_binary_path)
        output_path = filename + "_decompressed.txt"

        with open(input_binary_path, 'rb') as file:
            header_len = int.from_bytes(file.read(4), byteorder='big')
            header = eval(file.read(header_len).decode('utf-8'))
            
            # Reverse codes mapping for decoding
            self.reverse_mapping = {v: k for k, v in header.items()}
            
            bit_string = ""
            byte = file.read(1)
            while byte:
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
                byte = file.read(1)

        # Remove padding and decode bit stream
        padded_info = bit_string[:8]
        extra_padding = int(padded_info, 2)
        encoded_text = bit_string[8:]
        encoded_text = encoded_text[:-1*extra_padding] if extra_padding > 0 else encoded_text

        current_code = ""
        decoded_text = ""

        for bit in encoded_text:
            current_code += bit
            if current_code in self.reverse_mapping:
                character = self.reverse_mapping[current_code]
                decoded_text += character
                current_code = ""

        with open(output_path, 'w', encoding='utf-8') as output:
            output.write(decoded_text)

        print(f"Decompression successful! Output saved to: {output_path}")
        return output_path

# --- Driver Execution Example ---
if __name__ == "__main__":
    # Example usage:
    # 1. Create a sample text file to test
    sample_file = "sample.txt"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Project Fold Huffman coding algorithm implementation test text file. " * 50)

    # 2. Run Compressor
    huffman = HuffmanCompressor(sample_file)
    compressed_file = huffman.compress()

    # 3. Run Decompressor
    huffman.decompress(compressed_file)